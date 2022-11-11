import asyncio
import json
import time

from indy import anoncreds, did, ledger, pool, wallet, blob_storage
from indy.error import ErrorCode, IndyError


async def create_wallet(identity):
    print("\"{}\" -> Create wallet".format(identity['name']))
    try:
        await wallet.create_wallet(identity['wallet_config'],
                                   identity['wallet_credentials'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    identity['wallet'] = await wallet.open_wallet(identity['wallet_config'],
                                                  identity['wallet_credentials'])



async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    print(nym_request)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)


async def getting_verinym(from_, to):
    await create_wallet(to)

    (to['did'], to['key']) = await did.create_and_store_my_did(to['wallet'], "{}")

    from_['info'] = {
        'did': to['did'],
        'verkey': to['key'],
        'role': to['role'] or None
    }

    await send_nym(from_['pool'], from_['wallet'], from_['did'], from_['info']['did'],
                   from_['info']['verkey'], from_['info']['role'])



async def ensure_previous_request_applied(pool_handle, checker_request, checker):
    for _ in range(3):
        response = json.loads(await ledger.submit_request(pool_handle, checker_request))
        try:
            if checker(response):
                return json.dumps(response)
        except TypeError:
            pass
        time.sleep(5)


async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = \
        await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                              lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)



async def run():

    ###################################
    ############# Part-A ############## 
    ###################################
    
    pool_ = {
        'name': 'pool1'
    }
    print("Open Pool Ledger: {}".format(pool_['name']))
    pool_['genesis_txn_path'] = "pool1.txn"
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})

    print(pool_)

    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(2)

    try:
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    pool_['handle'] = await pool.open_pool_ledger(pool_['name'], None)

    print(pool_['handle'])

    #    --------------------------------------------------------------------------
    #  Accessing a steward.

    steward = {
        'name': "Sovrin Steward",
        'wallet_config': json.dumps({'id': 'sovrin_steward_wallet'}),
        'wallet_credentials': json.dumps({'key': 'steward_wallet_key'}),
        'pool': pool_['handle'],
        'seed': '000000000000000000000000Steward1'
    }
    print(steward)

    await create_wallet(steward)

    print(steward["wallet"])

    steward["did_info"] = json.dumps({'seed':steward['seed']})
    print(steward["did_info"])

    # did:demoindynetwork:Th7MpTaRZVRYnPiabds81Y
    steward['did'], steward['key'] = await did.create_and_store_my_did(steward['wallet'], steward['did_info'])

     # ----------------------------------------------------------------------
    # Create and register dids for Government, University and company
    # 
    print("\n\n\n==============================")
    print("==  Government registering Verinym  ==")
    print("------------------------------")


    government = {
        'name': 'Government',
        'wallet_config': json.dumps({'id': 'government_wallet'}),
        'wallet_credentials': json.dumps({'key': 'government_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    await getting_verinym(steward, government)


    print("==============================")
    print("== IIT Kharagpur getting Verinym  ==")
    print("------------------------------")

    theUniversity = {
        'name': 'IIT_Kharagpur',
        'wallet_config': json.dumps({'id': 'IIT_Kharagpur'}),
        'wallet_credentials': json.dumps({'key': 'IIT_Kharagpur'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    await getting_verinym(steward, theUniversity)

    #####################################################################################################################

    ###################################
    ############# Part-B ############## 
    ###################################

    # -----------------------------------------------------
    # Government creates PropertyDetails schema

    print("\"Government\" -> Create \"PropertyDetails\" Schema")
    property_details = {
        'name': 'PropertyDetails',
        'version': '1.0.0',
        'attributes': ['owner_first_name', 'owner_last_name', 'address_of_property', 'owner_since_year', 'property_value_estimate']
    }

    (government['property_details_schema_id'], government['property_details_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], property_details['name'], property_details['version'],
                                             json.dumps(property_details['attributes']))
    
    print(government['property_details_schema'])
    property_details_schema_id = government['property_details_schema_id']

    print(government['property_details_schema_id'], government['property_details_schema'])

    print("\"Government\" -> Send \"PropertyDetails\" Schema to Ledger")

    
    schema_request = await ledger.build_schema_request(government['did'], government['property_details_schema'])
    await ledger.sign_and_submit_request(government['pool'], government['wallet'], government['did'], schema_request)
    

    # -----------------------------------------------------
    # Government creates BonafideStudent schema

    bonafide_student = {
        'name': 'BonafideStudent',
        'version': '1.0.0',
        'attributes': ['student_first_name', 'student_last_name', 'degree_name', 'student_since_year', 'cgpa']
    }

    (government['bonafide_student_schema_id'], government['bonafide_student_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], bonafide_student['name'], bonafide_student['version'],
                                             json.dumps(bonafide_student['attributes']))
    
    print(government['bonafide_student_schema'])
    bonafide_student_schema_id = government['bonafide_student_schema_id']

    print(government['bonafide_student_schema_id'], government['bonafide_student_schema'])

    print("\"Government\" -> Send \"BonafideStudent\" Schema to Ledger")

    
    schema_request = await ledger.build_schema_request(government['did'], government['bonafide_student_schema'])
    await ledger.sign_and_submit_request(government['pool'], government['wallet'], government['did'], schema_request)
    
    # -----------------------------------------------------
    # IIT Kharagpur registers a credential definition for BonafideStudent
    
    print("\n\n==============================")
    print("=== IIT Kharagpur BonafideStudent Credential Definition Setup ==")
    print("------------------------------")

    print("\"IIT Kharagpur\" -> Get \"BonafideStudent\" Schema from Ledger")

    # GET SCHEMA FROM LEDGER
    get_schema_request = await ledger.build_get_schema_request(theUniversity['did'], bonafide_student_schema_id)
    get_schema_response = await ensure_previous_request_applied(
        theUniversity['pool'], get_schema_request, lambda response: response['result']['data'] is not None)
    (theUniversity['bonafide_student_schema_id'], theUniversity['bonafide_student_schema']) = await ledger.parse_get_schema_response(get_schema_response)

    # BONAFIDE_STUDENT CREDENTIAL DEFINITION
    print("\"IIT Kharagpur\" -> Create and store in Wallet \"IIT Kharagpur BonafideStudent\" Credential Definition")
    bonafide_student_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": False}
    }

    (theUniversity['bonafide_student_cred_def_id'], theUniversity['bonafide_student_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(theUniversity['wallet'], theUniversity['did'],
                                                               theUniversity['bonafide_student_schema'], bonafide_student_cred_def['tag'],
                                                               bonafide_student_cred_def['type'],
                                                               json.dumps(bonafide_student_cred_def['config']))

    print("\"IIT Kharagpur\" -> Send  \"IIT Kharagpur BonafideStudent\" Credential Definition to Ledger")
    # print(theUniversity['bonafide_student_cred_def'])

    cred_def_request = await ledger.build_cred_def_request(theUniversity['did'], theUniversity['bonafide_student_cred_def'])
    # print(cred_def_request)
    await ledger.sign_and_submit_request(theUniversity['pool'], theUniversity['wallet'], theUniversity['did'], cred_def_request)
    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", theUniversity['bonafide_student_cred_def_id'])


    # -----------------------------------------------------
    # the Government registers a credential definition for PropertyDetails.

    print("\n\n==============================")
    print("=== the Government PropertyDetails Credential Definition Setup ==")
    print("------------------------------")
    
    # GET SCHEMA FROM LEDGER
    get_schema_request = await ledger.build_get_schema_request(government['did'], property_details_schema_id)
    get_schema_response = await ensure_previous_request_applied(
        government['pool'], get_schema_request, lambda response: response['result']['data'] is not None)
    (government['property_details_schema_id'], government['property_details_schema']) = await ledger.parse_get_schema_response(get_schema_response)

    # PROPERTY_DETAILS CREDENTIAL DEFINITION
    print("\"Government\" -> Create and store in Wallet \"Government PropertyDetails\" Credential Definition")
    property_details_cred_def = {
        'tag': 'TAG2',
        'type': 'CL',
        'config': {"support_revocation": False}
    }
    (government['property_details_cred_def_id'], government['property_details_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(government['wallet'], government['did'],
                                                               government['property_details_schema'], property_details_cred_def['tag'],
                                                               property_details_cred_def['type'],
                                                               json.dumps(property_details_cred_def['config']))

    print("\"government\" -> Send  \"government PropertyDetails\" Credential Definition to Ledger")
    # print(government['property_details_cred_def'])

    cred_def_request = await ledger.build_cred_def_request(government['did'], government['property_details_cred_def'])
    # print(cred_def_request)
    await ledger.sign_and_submit_request(government['pool'], government['wallet'], government['did'], cred_def_request)
    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", government['property_details_cred_def_id'])

    #####################################################################################################################

    ###################################
    ############# Part-C ############## 
    ###################################

    # ------------------------------------------------------------
    #  Sunil setting up his wallet
    print("== Sunil setup ==")
    print("------------------------------")

    sunil = {
        'name': 'Sunil',
        'wallet_config': json.dumps({'id': 'sunil_wallet'}),
        'wallet_credentials': json.dumps({'key': 'sunil_wallet_key'}),
        'pool': pool_['handle'],
    }

    await create_wallet(sunil)
    (sunil['did'], sunil['key']) = await did.create_and_store_my_did(sunil['wallet'], "{}")

    # ------------------------------------------------------------
    #  Sunil getting PropertyDetails credential from Government
    print("==============================")
    print("=== Getting PropertyDetails with government ==")
    print("==============================")
    
    # Government creates PropertyDetails Credential offer

    print("\"government\" -> Create \"PropertyDetails\" Credential Offer for Sunil")
    government['property_details_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(government['wallet'], government['property_details_cred_def_id'])

    print("\"government\" -> Send \"PropertyDetails\" Credential Offer to Sunil")
    
    # Over Network 
    sunil['property_details_cred_offer'] = government['property_details_cred_offer']

    print(sunil['property_details_cred_offer'])

    # Sunil prepares a PropertyDetails credential request

    property_details_cred_offer_object = json.loads(sunil['property_details_cred_offer'])

    sunil['property_details_schema_id'] = property_details_cred_offer_object['schema_id']
    sunil['property_details_cred_def_id'] = property_details_cred_offer_object['cred_def_id']

    print("\"Sunil\" -> Create and store \"Sunil\" Master Secret in Wallet")
    sunil['master_secret_id'] = await anoncreds.prover_create_master_secret(sunil['wallet'], None)

    print("\"Sunil\" -> Get \"government PropertyDetails\" Credential Definition from Ledger")
    (sunil['property_details_cred_def_id'], sunil['property_details_cred_def']) = \
        await get_cred_def(sunil['pool'], sunil['did'], sunil['property_details_cred_def_id'])

    print("\"Sunil\" -> Create \"PropertyDetails\" Credential Request for government")
    (sunil['property_details_cred_request'], sunil['property_details_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(sunil['wallet'], sunil['did'],
                                                     sunil['property_details_cred_offer'],
                                                     sunil['property_details_cred_def'],
                                                     sunil['master_secret_id'])

    print("\"Sunil\" -> Send \"PropertyDetails\" Credential Request to government")

    # Over Network
    government['property_details_cred_request'] = sunil['property_details_cred_request']


    # government issues credential to Sunil ----------------
    print("\"government\" -> Create \"PropertyDetails\" Credential for Sunil")
    government['sunil_property_details_cred_values'] = json.dumps({
        "owner_first_name": {"raw": "Sunil", "encoded": "5893255682023721427"},
        "owner_last_name": {"raw": "Dey", "encoded": "1327274877492361491"},
        "address_of_property": {"raw": "M G Road, Chennai", "encoded": "2508559170611499072"},
        "owner_since_year": {"raw": "2005", "encoded": "2005"},
        "property_value_estimate": {"raw": "1000000", "encoded": "1000000"},
    })
    
    government['property_details_cred'], _, _ = \
        await anoncreds.issuer_create_credential(government['wallet'], government['property_details_cred_offer'],
                                                 government['property_details_cred_request'],
                                                 government['sunil_property_details_cred_values'], None, None)

    print("\"government\" -> Send \"PropertyDetails\" Credential to Sunil")
    print(government['property_details_cred'])
    # Over the network
    sunil['property_details_cred'] = government['property_details_cred']

    print("\"Sunil\" -> Store \"PropertyDetails\" Credential from government")
    _, sunil['property_details_cred_def'] = await get_cred_def(sunil['pool'], sunil['did'],
                                                         sunil['property_details_cred_def_id'])

    await anoncreds.prover_store_credential(sunil['wallet'], None, sunil['property_details_cred_request_metadata'],
                                            sunil['property_details_cred'], sunil['property_details_cred_def'], None)
    
    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", sunil['property_details_cred_def'])

    # ------------------------------------------------------------
    #  Sunil getting BonafideStudent credential from IIT Kharagpur

    print("==============================")
    print("=== Getting BonafideStudent with IIT Kharagpur ==")
    print("==============================")
    
    # IIT Kharagpur creates BonafideStudent Credential offer

    print("\"IIT Kharagpur\" -> Create \"BonafideStudent\" Credential Offer for Sunil")
    theUniversity['bonafide_student_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(theUniversity['wallet'], theUniversity['bonafide_student_cred_def_id'])

    print("\"IIT Kharagpur\" -> Send \"BonafideStudent\" Credential Offer to Sunil")
    
    # Over Network 
    sunil['bonafide_student_cred_offer'] = theUniversity['bonafide_student_cred_offer']

    print(sunil['bonafide_student_cred_offer'])

    # Sunil prepares a PropertyDetails credential request

    bonafide_student_cred_offer_object = json.loads(sunil['bonafide_student_cred_offer'])

    sunil['bonafide_student_schema_id'] = bonafide_student_cred_offer_object['schema_id']
    sunil['bonafide_student_cred_def_id'] = bonafide_student_cred_offer_object['cred_def_id']

    print("\"Sunil\" -> Create and store \"Sunil\" Master Secret in Wallet")
    sunil['master_secret_id'] = await anoncreds.prover_create_master_secret(sunil['wallet'], None)

    print("\"Sunil\" -> Get \"government BonafideStudent\" Credential Definition from Ledger")
    (sunil['bonafide_student_cred_def_id'], sunil['bonafide_student_cred_def']) = \
        await get_cred_def(sunil['pool'], sunil['did'], sunil['bonafide_student_cred_def_id'])

    print("\"Sunil\" -> Create \"BonafideStudent\" Credential Request for IIT Kharagpur")
    (sunil['bonafide_student_cred_request'], sunil['bonafide_student_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(sunil['wallet'], sunil['did'],
                                                     sunil['bonafide_student_cred_offer'],
                                                     sunil['bonafide_student_cred_def'],
                                                     sunil['master_secret_id'])

    print("\"Sunil\" -> Send \"BonafideStudent\" Credential Request to IIT Kharagpur")

    # Over Network
    theUniversity['bonafide_student_cred_request'] = sunil['bonafide_student_cred_request']

    # IIT Kharagpur issues credential to Sunil ----------------
    print("\"IIT Kharagpur\" -> Create \"BonafideStudent\" Credential for Sunil")
    theUniversity['sunil_bonafide_student_cred_values'] = json.dumps({
        "student_first_name": {"raw": "Sunil", "encoded": "5893255682023721427"},
        "student_last_name": {"raw": "Dey", "encoded": "1327274877492361491"},
        "degree_name": {"raw": "Mtech", "encoded": "1564044317497562940"},
        "student_since_year": {"raw": "2022", "encoded": "2022"},
        "cgpa": {"raw": "8", "encoded": "8"},
    })
    
    theUniversity['bonafide_student_cred'], _, _ = \
        await anoncreds.issuer_create_credential(theUniversity['wallet'], theUniversity['bonafide_student_cred_offer'],
                                                 theUniversity['bonafide_student_cred_request'],
                                                 theUniversity['sunil_bonafide_student_cred_values'], None, None)

    print("\"IIT Kharagpur\" -> Send \"BonafideStudent\" Credential to Sunil")
    print(theUniversity['bonafide_student_cred'])
    # Over the network
    sunil['bonafide_student_cred'] = theUniversity['bonafide_student_cred']

    print("\"Sunil\" -> Store \"BonafideStudent\" Credential from IIT Kharagpur")
    _, sunil['bonafide_student_cred_def'] = await get_cred_def(sunil['pool'], sunil['did'],
                                                         sunil['bonafide_student_cred_def_id'])

    await anoncreds.prover_store_credential(sunil['wallet'], None, sunil['bonafide_student_cred_request_metadata'],
                                            sunil['bonafide_student_cred'], sunil['bonafide_student_cred_def'], None)
    
    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", sunil['bonafide_student_cred_def'])


    #####################################################################################################################


    ###################################
    ############# Part-D ############## 
    ###################################

    #####################################################################################################################



loop = asyncio.get_event_loop()
loop.run_until_complete(run())

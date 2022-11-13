import asyncio
import json
import time

from indy import anoncreds, did, ledger, pool, wallet, blob_storage
from indy.error import ErrorCode, IndyError

from os.path import dirname


async def verifier_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp=None):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        print("\"{}\" -> Get Schema from Ledger".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        print("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            # Get Revocation Definitions and Revocation Registries
            print("\"{}\" -> Get Revocation Definition from Ledger".format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])

            get_revoc_reg_def_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

            print("\"{}\" -> Get Revocation Registry from Ledger".format(actor))
            if not timestamp: timestamp = item['timestamp']
            get_revoc_reg_request = \
                await ledger.build_get_revoc_reg_request(_did, item['rev_reg_id'], timestamp)
            get_revoc_reg_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, rev_reg_json, timestamp2) = await ledger.parse_get_revoc_reg_response(get_revoc_reg_response)

            rev_regs[rev_reg_id] = {timestamp2: json.loads(rev_reg_json)}
            rev_reg_defs[rev_reg_id] = json.loads(revoc_reg_def_json)

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)


async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ensure_previous_request_applied(
        pool_handle, get_schema_request, lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_schema_response(get_schema_response)


async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = \
        await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                              lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)



async def ensure_previous_request_applied(pool_handle, checker_request, checker):
    for _ in range(3):
        response = json.loads(await ledger.submit_request(pool_handle, checker_request))
        try:
            if checker(response):
                return json.dumps(response)
        except TypeError:
            pass
        time.sleep(5)


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


async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    print(nym_request)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)


async def get_credential_for_referent(search_handle, referent):
    credentials = json.loads(
        await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 10))
    
    # ### DEBUG
    # print("=================")
    # print(credentials)
    # print("=================")
    # #####
    
    return credentials[0]['cred_info']


async def prover_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp_from=None,
                                          timestamp_to=None):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    for item in identifiers.values():
        print("\"{}\" -> Get Schema from Ledger".format(actor))
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.", item['schema_id'])
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        print("\"{}\" -> Get Claim Definition from Ledger".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            # Create Revocations States
            print("\"{}\" -> Get Revocation Registry Definition from Ledger".format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])

            get_revoc_reg_def_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

            print("\"{}\" -> Get Revocation Registry Delta from Ledger".format(actor))
            if not timestamp_to: timestamp_to = int(time.time())
            get_revoc_reg_delta_request = \
                await ledger.build_get_revoc_reg_delta_request(_did, item['rev_reg_id'], timestamp_from, timestamp_to)
            get_revoc_reg_delta_response = \
                await ensure_previous_request_applied(pool_handle, get_revoc_reg_delta_request,
                                                      lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_delta_json, t) = \
                await ledger.parse_get_revoc_reg_delta_response(get_revoc_reg_delta_response)

            tails_reader_config = json.dumps(
                {'base_dir': dirname(json.loads(revoc_reg_def_json)['value']['tailsLocation']),
                 'uri_pattern': ''})
            blob_storage_reader_cfg_handle = await blob_storage.open_reader('default', tails_reader_config)

            print('%s - Create Revocation State', actor)
            rev_state_json = \
                await anoncreds.create_revocation_state(blob_storage_reader_cfg_handle, revoc_reg_def_json,
                                                        revoc_reg_delta_json, t, item['cred_rev_id'])
            rev_states[rev_reg_id] = {t: json.loads(rev_state_json)}

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)


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

    print("==============================")
    print("== CitiBank getting Verinym  ==")
    print("------------------------------")

    theCompany = {
        'name': 'CitiBank',
        'wallet_config': json.dumps({'id': 'CitiBank_wallet'}),
        'wallet_credentials': json.dumps({'key': 'CitiBank_wallet_key'}),
        'pool': pool_['handle'],
        'role': 'TRUST_ANCHOR'
    }

    await getting_verinym(steward, theCompany)

    #####################################################################################################################

    ###################################
    ############# Part-B ############## 
    ###################################

    # -----------------------------------------------------
    # Government creates PropertyDetails schema

    print("\"Government\" -> Create \"PropertyDetails\" Schema")
    property_details = {
        'name': 'PropertyDetails',
        'version': '1.2',
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
        'version': '1.2',
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
        'tag': 'TAG1',
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
        'wallet_config': json.dumps({'id': 'alice_wallet'}),
        'wallet_credentials': json.dumps({'key': 'alice_wallet_key'}),
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

    # print("\"Sunil\" -> Create and store \"Sunil\" Master Secret in Wallet")
    # sunil['master_secret_id'] = await anoncreds.prover_create_master_secret(sunil['wallet'], None)

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

    # Verifiable Presentation

    # Creating application request (presentaion request) --- validator - CitiBank
    print("\"CitiBank\" -> Create \"Loan Application\" Proof Request")
    nonce = await anoncreds.generate_nonce()

    theCompany['loan_application_proof_request'] = json.dumps({
        'nonce': nonce,
        'name': 'Loan-Application',
        'version': '0.1',
        'requested_attributes': {
            'attr1_referent': {
                'name': 'first_name'
            },
            'attr2_referent': {
                'name': 'last_name'
            },
            'attr3_referent': {
                'name': 'degree_name',
                'restrictions': [{'cred_def_id': theUniversity['bonafide_student_cred_def_id']}]
            },
            'attr4_referent': {
                'name': 'address_of_property',
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            },
            'attr5_referent': {
                'name': 'owner_since_year',
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            },
        },
        'requested_predicates': {
            'predicate1_referent': {
                'name': 'student_since_year',
                'p_type': '>',
                'p_value': 2021,
                'restrictions': [{'cred_def_id': theUniversity['bonafide_student_cred_def_id']}]
            },
            'predicate2_referent': {
                'name': 'cgpa',
                'p_type': '>',
                'p_value': 7,
                'restrictions': [{'cred_def_id': theUniversity['bonafide_student_cred_def_id']}]
            },
            'predicate3_referent': {
                'name': 'property_value_estimate',
                'p_type': '>',
                'p_value': 400000,
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            }
        }
    })

    print("\"CitiBank\" -> Send \"Loan-Application\" Proof Request to Sunil")

    # Over Network
    sunil['loan_application_proof_request'] = theCompany['loan_application_proof_request']
    
    print(sunil['loan_application_proof_request'])

    # Sunil prepares the presentation ===================================

    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", sunil['loan_application_proof_request'])

    print("\"Sunil\" -> Get credentials for \"Loan-Application\" Proof Request")

    search_for_loan_application_proof_request = \
        await anoncreds.prover_search_credentials_for_proof_req(sunil['wallet'],
                                                                sunil['loan_application_proof_request'], None)
    
    print("---------------------------")
    print(search_for_loan_application_proof_request)
    print("---------------------------")

    cred_for_attr1 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr1_referent')
    cred_for_attr2 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr2_referent')
    cred_for_attr3 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr3_referent')
    cred_for_attr4 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr4_referent')
    cred_for_attr5 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr5_referent')
    
    cred_for_predicate1 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate1_referent')
    cred_for_predicate2 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate2_referent')
    cred_for_predicate3 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate3_referent')
    
    print("---------------------------")
    print(cred_for_attr1)
    print("---------------------------")


    await anoncreds.prover_close_credentials_search_for_proof_req(search_for_loan_application_proof_request)

    sunil['creds_for_loan_application_proof'] = {cred_for_attr1['referent']: cred_for_attr1,
                                                cred_for_attr2['referent']: cred_for_attr2,
                                                cred_for_attr3['referent']: cred_for_attr3,
                                                cred_for_attr4['referent']: cred_for_attr4,
                                                cred_for_attr5['referent']: cred_for_attr5,
                                                cred_for_predicate1['referent']: cred_for_predicate1,
                                                cred_for_predicate2['referent']: cred_for_predicate2,
                                                cred_for_predicate3['referent']: cred_for_predicate3}

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(sunil['creds_for_loan_application_proof'])

    sunil['schemas_for_loan_application'], sunil['cred_defs_for_loan_application'], \
    sunil['revoc_states_for_loan_application'] = \
        await prover_get_entities_from_ledger(sunil['pool'], sunil['did'],
                                              sunil['creds_for_loan_application_proof'], sunil['name'])


    print("\"Sunil\" -> Create \"Loan-Application\" Proof")
    sunil['loan_application_requested_creds'] = json.dumps({
        'self_attested_attributes': {
            'attr1_referent': 'Sunil',
            'attr2_referent': 'Dey',
        },
        'requested_attributes': {
            'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True},
            'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True},
            'attr5_referent': {'cred_id': cred_for_attr5['referent'], 'revealed': True},
        },
        'requested_predicates': {
            'predicate1_referent': {'cred_id': cred_for_predicate1['referent']},
            'predicate2_referent': {'cred_id': cred_for_predicate2['referent']},
            'predicate3_referent': {'cred_id': cred_for_predicate3['referent']},
        }
    })

    sunil['loan_application_proof'] = \
        await anoncreds.prover_create_proof(sunil['wallet'], sunil['loan_application_proof_request'],
                                            sunil['loan_application_requested_creds'], sunil['master_secret_id'],
                                            sunil['schemas_for_loan_application'],
                                            sunil['cred_defs_for_loan_application'],
                                            sunil['revoc_states_for_loan_application'])
    print(sunil['loan_application_proof'])

    print("\"Sunil\" -> Send \"Loan-Application\" Proof to CitiBank")

    # Over Network
    theCompany['loan_application_proof'] = sunil['loan_application_proof']
    
    # Validating the verifiable presentation
    loan_application_proof_object = json.loads(theCompany['loan_application_proof'])

    theCompany['schemas_for_loan_application'], theCompany['cred_defs_for_loan_application'], \
    theCompany['revoc_ref_defs_for_loan_application'], theCompany['revoc_regs_for_loan_application'] = \
        await verifier_get_entities_from_ledger(theCompany['pool'], theCompany['did'],
                                                loan_application_proof_object['identifiers'], theCompany['name'])

    print("\"CitiBank\" -> Verify \"Loan-Application\" Proof from Sunil")
    
    #####################################
    ####### Changes left   ##############
    #####################################
    assert 'Sunil' == loan_application_proof_object['requested_proof']['self_attested_attrs']['attr1_referent']
    assert 'Dey' == loan_application_proof_object['requested_proof']['self_attested_attrs']['attr2_referent']
    assert 'Mtech' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw']
    assert 'M G Road, Chennai' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']
    assert '2005' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr5_referent']['raw']

    assert await anoncreds.verifier_verify_proof(theCompany['loan_application_proof_request'], theCompany['loan_application_proof'],
                                                 theCompany['schemas_for_loan_application'],
                                                 theCompany['cred_defs_for_loan_application'],
                                                 theCompany['revoc_ref_defs_for_loan_application'],
                                                 theCompany['revoc_regs_for_loan_application'])


    #####################################################################################################################



loop = asyncio.get_event_loop()
loop.run_until_complete(run())

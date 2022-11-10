const {Wallets, Gateway} = require('fabric-network')
const FabricCAServices = require('fabric-ca-client')
const { buildCAClient, registerAndEnrollUser, enrollAdmin } = require('../test-application/javascript/CAUtil.js');
const { buildCCPOrg1, buildWallet } = require('../test-application/javascript/AppUtil.js');
const fs = require('fs')
const path = require('path')
const channelName = 'mychannel';
const chaincodeName = 'p1';
const mspOrg1 = 'Org1MSP';
const walletPath = path.join(__dirname, 'wallet');
const org1UserId = 'appUser';

function prettyJSONString(inputString) {
	return JSON.stringify(JSON.parse(inputString), null, 2);
}

async function main(){

    // Org1 connection profile
    var ccp = buildCCPOrg1();

    // Org1 Ca
    const caClient = buildCAClient(FabricCAServices, ccp, 'ca.org1.example.com');

    // Create a wallet instance
    const wallet = await buildWallet(Wallets, walletPath);

    // Enroll the admin
    await enrollAdmin(caClient, wallet, mspOrg1);

    // Register a user
    await registerAndEnrollUser(caClient, wallet, mspOrg1, org1UserId, 'org1.department1');

    // Connect to gateway
    const gateway = new Gateway();
    await gateway.connect(ccp, {wallet, identity:org1UserId, discovery: {enabled:true, asLocalhost: true}})
    
    // Connect to channel
    const network = await gateway.getNetwork(channelName)
    
    // Select the contract
    const contract = network.getContract(chaincodeName)

    // Query and Invoke transactions
    try {
        await contract.submitTransaction("CreateStudent", "19CS30014", "D Saha")
        console.log("Insert Query Committed.")
    } catch(err) {
        console.log(`Insert Query [Caught exception] : ${err}`)
    }

    
    try {
        // should show : D Saha
        let result = await contract.evaluateTransaction("ReadStudent", "19CS30014")
        console.log(`Successful Lookup Query: ${result}`)
    } catch(err) {
        console.log(`Successful Lookup Query [Caught exception] : ${err}`)
    }

    try {
        // should show error
        result = await contract.evaluateTransaction("ReadStudent", "19CS10049")
        console.log(`Unsuccessful Lookup Query: ${result}`)
    } catch(err) {
        console.log(`Unsuccessful Lookup Query [Caught exception] : ${err}`)
    } finally {
        gateway.disconnect();
    }
}

main();
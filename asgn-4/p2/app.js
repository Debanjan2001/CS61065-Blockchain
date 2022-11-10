const {Wallets, Gateway} = require('fabric-network')
const FabricCAServices = require('fabric-ca-client')
const { buildCAClient, registerAndEnrollUser, enrollAdmin } = require('../test-application/javascript/CAUtil.js');
const { buildCCPOrg1, buildCCPOrg2, buildWallet } = require('../test-application/javascript/AppUtil.js');
const fs = require('fs')
const path = require('path')
const readline = require("readline-sync")

const channelName = 'mychannel';
const chaincodeName = 'p2';
const mspOrg1 = 'Org1MSP';
const mspOrg2 = 'Org2MSP';
const walletPathOrg1 = path.join(__dirname, 'wallet', 'org1');
const walletPathOrg2 = path.join(__dirname, 'wallet', 'org2');
const org1UserId = 'app1User';
const org2UserId = 'app2User';

function prettyJSONString(inputString) {
	return JSON.stringify(JSON.parse(inputString), null, 2);
}

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
} 
  

async function main(){

    /**
     * Setup for Organization 1
     */
    // Org1 connection profile
    const ccp_1 = buildCCPOrg1();

    // Org1 Ca
    const caClient_1 = buildCAClient(FabricCAServices, ccp_1, 'ca.org1.example.com');

    // Create a wallet instance
    const wallet_1 = await buildWallet(Wallets, walletPathOrg1);

    // Enroll the admin
    await enrollAdmin(caClient_1, wallet_1, mspOrg1);

    // Register a user
    await registerAndEnrollUser(caClient_1, wallet_1, mspOrg1, org1UserId, 'org1.department1');

    // Connect to gateway
    const gateway_1 = new Gateway();
    await gateway_1.connect(ccp_1, {wallet: wallet_1, identity: org1UserId, discovery: {enabled:true, asLocalhost: true}});
    
    // Connect to network channel
    const network_1 = await gateway_1.getNetwork(channelName)
    // select the contract
    const contract_1 = network_1.getContract(chaincodeName)

    /**
     * Setup for Organization 2
     */
    // Org2 connection profile
    var ccp_2 = buildCCPOrg2();

    // Org2 Ca
    const caClient_2 = buildCAClient(FabricCAServices, ccp_2, 'ca.org2.example.com');

    // Create a wallet instance
    const wallet_2 = await buildWallet(Wallets, walletPathOrg2);

    // Enroll the admin
    await enrollAdmin(caClient_2, wallet_2, mspOrg2);

    // Register a user
    await registerAndEnrollUser(caClient_2, wallet_2, mspOrg2, org2UserId, 'org2.department1');

    // Connect to gateway
    const gateway_2 = new Gateway();
    await gateway_2.connect(ccp_2, {wallet: wallet_2, identity: org2UserId, discovery: {enabled:true, asLocalhost: true}});
    
    // Connect to network channel
    const network_2 = await gateway_2.getNetwork(channelName)
    // select the contract
    const contract_2 = network_2.getContract(chaincodeName)


    // const rl = readline.createInterface({
    //     input: process.stdin,
    //     output: process.stdout,
    // });

    var peerTurn = 0;
    var readNext = 1;
    console.log("Starting test utility, invalid commands will terminate the program... ")
    while(readNext) {
        // default initialization
        let contract = contract_1
        let cmd_str = ""

        // select the current peer contract and which peer to execute the next command
        if(peerTurn == 1) {
            contract = contract_2  
        } else { // peerTurn == 0
            contract = contract_1
        }
        peerTurn = 1 - peerTurn

        // read the input command
        cmd_str = readline.question("Enter command : ");

        // console.log(cmd_str);

        if(cmd_str == "INSERT") {
            var value = 0;
            let str = readline.question("Enter value : ");
            value = parseInt(str);
            // testInsert(contract, value);
            try {
                await contract.submitTransaction("Insert", value.toString());
                console.log(`Insert(${value}) successful.`);
            } catch(err) {
                console.log(`Insert [Caught exception] : ${err}`);
            }

        } else if(cmd_str == "DELETE") {
            var value = 0;
            let str = readline.question("Enter value : ");
            value = parseInt(str);
            // testDelete(contract, value);
            try {
                await contract.submitTransaction("Delete", value.toString());
                console.log(`Delete(${value}) successful.`);
            } catch(err) {
                console.log(`Delete [Caught exception] : ${err}`);
            }
        } else if(cmd_str == "INORDER") {
            // testInorder(contract);
            try {
                let result = await contract.evaluateTransaction("Inorder");
                console.log(`Inorder() : ${result.toString()}`);
            } catch(err) {
                console.log(`Inorder [Caught exception] : ${err}`);
            }
        } else if(cmd_str == "PREORDER") {
            // testPreorder(contract);
            try {
                let result = await contract.evaluateTransaction("Preorder");
                console.log(`Preorder() : ${result.toString()}`);
            } catch(err) {
                console.log(`Preorder [Caught exception] : ${err}`);
            }
        } else if(cmd_str == "TREEHEIGHT") {
            // testTreeheight(contract);
            try {
                let result = await contract.evaluateTransaction("TreeHeight");
                console.log(`TreeHeight() : ${result}`);
            } catch(err) {
                console.log(`TreeHeight [Caught exception] : ${err}`);
            }
        } else if(cmd_str == "EXIT") {
            readNext = 0;
            gateway_1.disconnect();
            gateway_2.disconnect();
            break;
        } else {
            console.log("Invalid command.")
            continue;
        }

        // sleep for about 2 seconds between each command 
        await delay(2000);  
    }
}

main();
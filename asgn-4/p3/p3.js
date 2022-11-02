const FabricCAServices = require('fabric-ca-client')
const {Wallets, Gateway} = require('fabric-network')
const fs = require('fs')
const path = require('path')

// async function main(){
// }

// main()

// Org1 connection profile
const ccpPath = path.resolve('../organizations/peerOrganizations/org1.example.com/connection-org1.json')
const ccp = JSON.parse(fs.readFileSync(ccpPath, 'utf8'))

// Org1 Ca
const caInfo = ccp.certificateAuthorities['ca.org1.example.com']
const caTLSCACerts = caInfo.tlsCACerts.pem
const ca = new FabricCAServices(caInfo.url, { trustedRoots: caTLSCACerts, verify: false }, caInfo.caName)



// Get admin identity
const admin_enrollment = await ca.enroll({ enrollmentID: 'admin', enrollmentSecret:'adminpw' });
const admin_x509Identity = {
    credentials: {
        certificate: enrollment.certificate,
        privateKey: enrollment.key.toBytes(),
    },
    mspId: 'Org1MSP',
    type: 'X.509',
};
await wallet.put("admin", x509Identity)
console.log("Admin enrolled and saved into wallet successfully")
adminIdentity = await wallet.get("admin")

// Register user for this app
const provider = wallet.getProviderRegistry().getProvider(adminIdentity.type);
const adminUser = await provider.getUserContext(adminIdentity, 'admin');
const secret = await ca.register(
    {affiliation: 'org1.department1', enrollmentID:'appUser', role: 'client'}, 
    adminUser
);

const user1_enrollment = await ca.enroll({enrollmentID: 'appUser',enrollmentSecret: secret});
const user1_x509Identity = {
    credentials: {
        certificate: enrollment.certificate,privateKey: enrollment.key.toBytes()
    },
    mspId: 'Org1MSP',
    type: 'X.509',
};

await wallet.put('appUser', x509Identity)
console.log("Enrolled appUser and saved to wallet")
userIdentity = await wallet.get("appUser")


// Connect to gateway
const gateway = new Gateway();
await gateway.connect(ccp, {wallet, identity:'appUser', discovery: {enabled:true, asLocalhost: true}})
// connect to channel
const network = await gateway.getNetwork('mychannel')
// select the contract
const contract = network.getContract("p1")


// Query and Invoke transactions
await contract.submitTransaction("CreateStudent", "19CS30014", "Debanjan Saha")
console.log("First query:", result.toString())
var result = await contract.evaluateTransaction("ReadStudent", "19CS30014")
console.log("Second query:", result.toString())
// disconnect
await gateway.disconnect()
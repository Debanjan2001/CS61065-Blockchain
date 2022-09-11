const Web3 = require('web3');
const fs = require('fs');
const smartContractABI = JSON.parse(fs.readFileSync("generated_abi.json"));

const privateKeyLocation = "/home/bob/.ethereum/goerli/keystore/UTC--2022-09-10T19-34-02.354154710Z--918ebc0ab5918990827bf6aaadd398dc77a68489";
const senderAddress = "0x918ebc0ab5918990827bf6aaadd398dc77a68489";
const smartContractAddress = "0x709830edf8feF92B0d879dE9ee9BdB2400BB5662";
const myPassword = "123";

const queryRollAddress = "0x8AF72Ec4f53704FfF24737f0445ddB40483eebd1";
const myRoll = "19CS30014";

async function main(){
	const serviceProviderURL = "https://goerli.infura.io/v3/f035d3e9459b4b25bf8836d944f466cb";
	const web3 = new Web3(
		new Web3.providers.HttpProvider(
			serviceProviderURL
		)
	);
		
	const privateKey = JSON.parse(fs.readFileSync(
		privateKeyLocation
	));

	const signer = web3.eth.accounts.decrypt(privateKey, myPassword);
	const contract = new web3.eth.Contract(
		smartContractABI, 
    	smartContractAddress,
		{
			from : signer.address,
		}
	);
		
	var gasLimit = await web3.eth.estimateGas({
		from : signer.address
	});
	console.log(gasLimit);
	console.log(web3.utils.toHex(gasLimit));

		
	const transaction = await {
		from : signer.address,
		to : smartContractAddress,
		gas : web3.utils.toHex(gasLimit),
		data : contract.methods.update(myRoll).encodeABI()
	};
	
	const signedTransaction = await web3.eth.accounts.signTransaction(
		transaction,
		signer.privateKey
	);

	const rawTx = signedTransaction.rawTransaction;

	await contract.methods.get(queryRollAddress).call().then(function(output) {
		console.log(output);
	});

	web3.eth.sendSignedTransaction(rawTx).then(function(output){
		console.log(output);
	})

	console.log("Calling getmine:\n");
	await contract.methods.getmine().call().then(function (output){
		console.log(output);
	});
}


main();

// function mainActivity(){

// 	myContract.methods.get(queryRollAddress).call().then(function(output) {
// 		console.log(output);
// 	});

// 	myContract.methods.update(myRoll).call().then(function(output){
// 		console.log(output);
// 	});

	
// 	myContract.methods.getmine().call().then(function(output){
// 		console.log(output);
// 	});

// };


// mainActivity();

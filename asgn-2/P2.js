var Web3 = require('web3');

const serviceProviderURL = "https://goerli.infura.io/v3/f035d3e9459b4b25bf8836d944f466cb";
// const serviceProviderURL = "http://localhost:8545";

// var web3 = new Web3(serviceProviderURL);
// console.log("Balance: ");
// web3.eth.getBalance("0x35F18427567108F800BDC2784277B9246eED37fA").then(console.log);

var Contract = require('web3-eth-contract');
Contract.setProvider(new Web3.providers.HttpProvider(serviceProviderURL));

const smartContractABI = [
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "addr",
				"type": "address"
			}
		],
		"name": "get",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getmine",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "roll",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "newRoll",
				"type": "string"
			}
		],
		"name": "update",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
];

const smartContractAddress = "0x709830edf8feF92B0d879dE9ee9BdB2400BB5662";

var myContract = new Contract(
    smartContractABI, 
    smartContractAddress,
    {
        "from": "918ebc0ab5918990827bf6aaadd398dc77a68489",
    },
);

const queryRollAddress = "0x8AF72Ec4f53704FfF24737f0445ddB40483eebd1";

myContract.methods.get(queryRollAddress).call().then(function(output) {
    console.log(output);
});

const myRoll = "19CS30014";

myContract.methods.update(myRoll).call().then(function(output){
    console.log(output);
});

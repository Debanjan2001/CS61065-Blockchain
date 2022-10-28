package main

import (
	"fmt"
	"encoding/json"
	"log"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing an Asset
type SmartContract struct {
	contractapi.Contract
}

type Student struct {
	roll 	string	`json:"Roll No."`
	name	string	`json:"Name"`
}

func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	// Left
	return nil;
}

func CreateStudent(ctx contractapi.TransactionContextInterface, roll string, name string) error {
	
}




  
  




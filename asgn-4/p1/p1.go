package main

import (
	"fmt"
	"encoding/json"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing an Student
type SmartContract struct {
	contractapi.Contract
}

type Student struct {
	Roll 	string	`json:"Roll"`
	Name	string	`json:"Name"`
}

func (s *SmartContract) CreateStudent(ctx contractapi.TransactionContextInterface, roll string, name string) error {
	exists, err := s.StudentExists(ctx, roll)
	if err != nil {
		return err
	}

	if exists {
		return fmt.Errorf("Student with roll %s Already exists", roll)
	}

	student := Student{
		Roll: roll,
		Name: name,
	}

	studentJSON, err := json.Marshal(student)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(roll, studentJSON)
}

func (s* SmartContract) StudentExists(ctx contractapi.TransactionContextInterface, roll string)(bool, error) {
	studentJSON, err := ctx.GetStub().GetState(roll)
	if err != nil {
		return false, fmt.Errorf("Failed to read from world state: %v", err)
	}

	return (studentJSON != nil), nil
}

func (s *SmartContract) ReadStudent(ctx contractapi.TransactionContextInterface, roll string)(string, error) {
	studentJSON, err := ctx.GetStub().GetState(roll)
	if err != nil {
		return "", fmt.Errorf("Failed to read from world state: %v", err)
	}

	if studentJSON == nil {
		return "", fmt.Errorf("The student %s does not exist", roll)
	}

	var student Student
	err = json.Unmarshal(studentJSON, &student)
	if err != nil {
	  return "", err
	}
  
	return student.Name, nil
}

func (s* SmartContract) ReadAllStudents(ctx contractapi.TransactionContextInterface)([][2] string, error) {
	studentsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}

	defer studentsIterator.Close()

	var students [][2]string
	
	for studentsIterator.HasNext() {
		studentResponse, err := studentsIterator.Next()
		if err != nil {
			return nil, err
		}
		var student Student
		err = json.Unmarshal(studentResponse.Value, &student)
		if err != nil {
			return nil, err
		}

	    var	studentData = [2]string{
			student.Roll, student.Name,
		}

		students = append(students, studentData)
	}
	return students, nil;
}

func main(){
	chaincode, err := contractapi.NewChaincode(new(SmartContract))
	if err != nil {
		fmt.Printf("Error creating chaincode: %s", err.Error())
		return
	}
	err = chaincode.Start();
	if err != nil {
		fmt.Printf("Error starting chaincode: %s", err.Error())
	}
}
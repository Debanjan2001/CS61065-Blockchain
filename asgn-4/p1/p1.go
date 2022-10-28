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
	name	string	`json:"Name"`
	roll 	string	`json:"Roll"`
}

func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	// Left
	return nil;
}

func (s *SmartContract) CreateStudent(ctx contractapi.TransactionContextInterface, roll string, name string) error {
	exists, err := s.StudentExists(ctx, roll)
	if err != nil {
		return err
	}

	if exists {
		return fmt.err("Student with roll %s Already exists", roll)
	}

	student = Student{
		name: name,
		roll: roll,
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
		return nil, fmt.Errorf("The student %s does not exist", roll)
	}

	var student Student
	err = json.Unmarshal(studentJSON, &student)
	if err != nil {
	  return nil, err
	}
  
	return student.name, nil
}

func (s* SmartContract) ReadAllStudents(ctx contractapi.TransactionContextInterface)([][2] string, error) {
	studentsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}

	defer studentsIterator.Close()

	var students [][2]string
	
	for studentsIterator.hasNext() {
		studentResponse, err := studentsIterator.Next()
		if err != nil {
			return nil, err
		}
		var student Student
		err := json.Unmarshal(studentResponse.Value, &student)
		if err != nil {
			return nil, err
		}

		studentData = [2]string{
			student.roll, student.name,
		}

		students = append(students, studentData)
	}
	return students, nil;
}




  
  




package main

import (
	"fmt"
	"encoding/json"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing a BST
type SmartContract struct {
	contractapi.Contract
}

type TreeNode struct {
	Val		int			`json:"Val"`
	Left 	*TreeNode	`json:"Left"`
	Right 	*TreeNode	`json:"Right"`
}

type MyBST struct {
	PrimaryKey 	string 		`json:"PrimaryKey"`
	Root 		*TreeNode 	`json:"Root"`
}

func (s* SmartContract)Insert(ctx contractapi.TransactionContextInterface, val int) error {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return err
	}

	if bst != nil {
		err := s.UpdateMyBST(ctx, val, MyBST, InsertValue())
		if err != nil {
			return err
		}
		return nil 
	}


	var node = TreeNode{
		val: val,
		Left: nil,
		Right: nil,
	} 

	bst_pk := "19CS30014-19CS10048"
	var bst = MyBST{
		PrimaryKey: bst_pk,
		Root: &node,
	}

	bstJSON, err := json.Marshal(bst)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(bst_pk, bstJSON) 
}

func Delete(ctx contractapi.TransactionContextInterface, val int) error {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return err
	}

	if bst != nil {
		
	}
}


func Preorder(ctx contractapi.TransactionContextInterface) (string, error) {

}

func Inorder(ctx contractapi.TransactionContextInterface) (string, error) {

}

func TreeHeight(ctx contractapi.TransactionContextInterface) (string, error) {

}

func MyBSTExists(ctx contractapi.TransactionContextInterface, key string) (bool, error) {

}

func ReadMyBST(ctx contractapi.TransactionContextInterface) (*MyBST, error) {
	
}

func UpdateMyBST(ctx contractapi.TransactionContextInterface, val int, bst *MyBST, operation int) error {

}

func InsertValue() int {
	return 0	
}

func DeleteValue() int {
	return 1
}


func preorderTraversal() {

}

func inorderTraversal() {

}

func heightOfTree() {

}
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

const pk = "19CS30014-19CS10048"

func (s* SmartContract)Insert(ctx contractapi.TransactionContextInterface, val int) error {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return err
	}

	if bst != nil {
		err := s.UpdateMyBST(ctx, val, bst, 0)
		if err != nil {
			return err
		}
		return nil 
	}

	var node = TreeNode{
		Val: val,
		Left: nil,
		Right: nil,
	} 

	bst_pk := pk
	var mybst = MyBST{
		PrimaryKey: bst_pk,
		Root: &node,
	}

	bstJSON, err := json.Marshal(mybst)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(bst_pk, bstJSON) 
}

func (s* SmartContract)Delete(ctx contractapi.TransactionContextInterface, val int) error {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return err
	}

	if bst == nil {
		return fmt.Errorf("The tree is not found")
	}

	err = s.UpdateMyBST(ctx, val, bst, 1)

	if err != nil {
		return err
	}

	return nil
}


func Preorder(ctx contractapi.TransactionContextInterface) (string, error) {

}

func Inorder(ctx contractapi.TransactionContextInterface) (string, error) {
}

func TreeHeight(ctx contractapi.TransactionContextInterface) (string, error) {

}

func MyBSTExists(ctx contractapi.TransactionContextInterface, key string) (bool, error) {

}

func (s* SmartContract)ReadMyBST(ctx contractapi.TransactionContextInterface) (*MyBST, error) {
	bstJSON, err := ctx.GetStub().GetState(pk)
	if err != nil {
		return nil, fmt.Errorf("Failed to read from world state: %v", err)
	}

	if bstJSON == nil {
		return nil, fmt.Errorf("The bst with primary key %s does not exist", pk)
	}

	var bst *MyBST
	err = json.Unmarshal(bstJSON, &bst)
	if err != nil {
	  return nil, err
	}
	
	return bst, nil
}

func (s* SmartContract)UpdateMyBST(ctx contractapi.TransactionContextInterface, val int, bst *MyBST, operation int) error {

	if operation == 0 {

	}else if operation == 1{

	}else {
		return fmt.Errorf("Illegal Operation in UpdateMyBST()")
	}
}

func InsertValue(bst *MyBST, val int) error {

	return nil
}

func DeleteValue(bst *MyBST, val int) error {
	return nil
}


func preorderTraversal(node *TreeNode, order []int) {
	if node == nil {
		return 
	}

	order = append(order, node.Val)
	preorderTraversal(node.Left, order)
	preorderTraversal(node.Right, order)
}

func inorderTraversal(node *TreeNode, order []int) {
	if node == nil {
		return 
	}

	inorderTraversal(node.Left, order)
	order = append(order, node.Val)
	inorderTraversal(node.Right, order)
}

func heightOfTree() {

}
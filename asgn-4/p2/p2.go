// Blockchain Assignment - 4
// Name: Debanjan Saha + Pritkumar Godhani
// Roll: 19CS30014     + 19CS10048

package main

import (
	"fmt"
	"encoding/json"
	"strconv"
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
	// if err != nil {
	// 	return err
	// }

	if bst != nil {
		err := s.UpdateMyBST(ctx, val, bst, 0)
		if err != nil {
			return err
		}
		return nil 
	}
	
	bst_pk := pk
	var mybst = MyBST{
		PrimaryKey: bst_pk,
		Root: &TreeNode{ Val: val, Left: nil,Right: nil,},
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

	err = s.UpdateMyBST(ctx, val, bst, 1)

	if err != nil {
		return err
	}

	return nil
}
func preorderTraversal(node *TreeNode, str string) string {
	if node == nil {
		return str
	}

	if str == "" {
		str = strconv.Itoa(node.Val)
	} else {
		str = str + "," + strconv.Itoa(node.Val)
	}

	str = preorderTraversal(node.Left, str)
	str = preorderTraversal(node.Right, str)
	return str
}

func inorderTraversal(node *TreeNode, str string) string  {
	if node == nil {
		return str
	}
	str = inorderTraversal(node.Left, str)
	if str == "" {
		str = strconv.Itoa(node.Val)
	} else {
		str = str + "," + strconv.Itoa(node.Val)
	}
	str = inorderTraversal(node.Right, str)
	return str	
}


func (s* SmartContract)Preorder(ctx contractapi.TransactionContextInterface) (string, error) {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return "", err
	}
	
	return preorderTraversal(bst.Root, ""), nil
}

func (s* SmartContract)Inorder(ctx contractapi.TransactionContextInterface) (string, error) {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return "", err
	}

	return inorderTraversal(bst.Root, ""), nil
}

func (s* SmartContract)TreeHeight(ctx contractapi.TransactionContextInterface) (string, error) {
	bst, err := s.ReadMyBST(ctx)
	if err != nil {
		return "0", err
	}

	ht := heightOfTree(bst.Root) 
	return strconv.Itoa(ht), nil
}

func MyBSTExists(ctx contractapi.TransactionContextInterface, key string) (bool, error) {
	// No need for now, will write later
	return false, nil
}

func (s* SmartContract)ReadMyBST(ctx contractapi.TransactionContextInterface) (*MyBST, error) {
	bstJSON, err := ctx.GetStub().GetState(pk)
	if bstJSON == nil {
		return nil, err
	}
	if err != nil {
		return nil, fmt.Errorf("Failed to read from world state: %v", err)
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
		bst.Root.InsertValue(val)
		newbst := MyBST{
			PrimaryKey: pk,
			Root: bst.Root,
		}

		bstJSON, err := json.Marshal(newbst)
		if err != nil {
			return err
		}
		return ctx.GetStub().PutState(pk, bstJSON)
	}else if operation == 1{
		bst.Root = bst.Root.DeleteValue(val)
		err := ctx.GetStub().DelState(pk)
		if err != nil {
			return err
		}
		newbst := MyBST{
			PrimaryKey: pk,
			Root:       bst.Root,
		}
		bstJSON, err := json.Marshal(newbst)
		if err != nil {
			return err
		}
		return ctx.GetStub().PutState(pk, bstJSON)
	}else {
		return fmt.Errorf("Illegal Operation in UpdateMyBST()")
	}
	return nil
}

func (node *TreeNode) InsertValue(val int) {
	if node == nil {
		return
	} else if val == node.Val {
		return
	} else if val < node.Val {
		if node.Left == nil {
			node.Left = &TreeNode{Val: val, Left: nil, Right: nil}
		} else {
			node.Left.InsertValue(val)
		}
	} else {
		if node.Right == nil {
			node.Right = &TreeNode{Val: val, Left: nil, Right: nil}
		} else {
			node.Right.InsertValue(val)
		}
	}
}

func getSuccessorNode(node *TreeNode) *TreeNode {
	var cur *TreeNode = node

	for (cur != nil && cur.Left != nil){
		cur = cur.Left
	}

	return cur
}

func (node *TreeNode)DeleteValue(val int) *TreeNode {
	if node == nil {
		return node
	}

	if val < node.Val {
		node.Left = node.Left.DeleteValue(val)
	}else if val > node.Val {
		node.Right = node.Right.DeleteValue(val)
	}else {
		if node.Left == nil && node.Right == nil{
			return nil
		}else if node.Left == nil{
			var newNode *TreeNode = node.Right
			return newNode
		}else if node.Right == nil{
			var newNode *TreeNode = node.Left
			return newNode
		}

		var successor *TreeNode = getSuccessorNode(node.Right)
		node.Val = successor.Val
		node.Right = node.Right.DeleteValue(successor.Val)
	}

	return node
}

func max(a int, b int) int {
	if a > b {
		return a
	}
	return b
}

func heightOfTree(node *TreeNode) int{
	if node == nil {
		return 0
	}

	return 1 + max(heightOfTree(node.Left), heightOfTree(node.Right))
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
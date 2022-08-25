import hashlib

FIXED_BLOCK_VERSION =  '02000000'

def generate_hash(value):
    hash_value = hashlib.md5(str(value).encode('utf-8')).hexdigest()
    return hash_value

class MerkleTreeNode:
    def __init__(self, value, left_child=None, right_child=None):
        self.left_child = left_child
        self.right_child = right_child
        self.value = value

    def copy(self):
        return MerkleTreeNode(self.value, self.left_child, self.right_child)
    
def generate_tree(transactions):
    leaves = [ MerkleTreeNode(generate_hash(value)) for value in transactions ]
    root = build_tree(leaves)
    return root

def build_tree(nodes):

    while(len(nodes) >  1):
        parents = []

        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1].copy())

        for i in range(0, len(nodes), 2):
            left_child = nodes[i]
            right_child = nodes[i+1]
            root = MerkleTreeNode(
                value=generate_hash(left_child.value+right_child.value),
                left_child=left_child,
                right_child=right_child,
            )
            parents.append(root)
        
        nodes = parents

    return nodes[0]

class Block:
    def __init__(self, prev_block_hash, merkle_root):
        self.block_version = FIXED_BLOCK_VERSION
        self.prev_block_hash = prev_block_hash
        self.merkle_root = merkle_root
        self.hash_value = self.generate_block_hash()

    def generate_block_hash(self):
        return generate_hash(self.block_version + self.prev_block_hash + self.merkle_root.value)


if __name__ == '__main__':

    genesis_block = Block("", generate_tree(["coinbase"]))
    previous_block = genesis_block

    blocks = int(input())
    for b in range(blocks):
        num_transactions = int(input())
        transactions = [ str(input()) for i in range(num_transactions) ]
        md5_hash = str(input())
        merkle_root = generate_tree(transactions)
        current_block = Block(
            prev_block_hash=previous_block.hash_value, 
            merkle_root=merkle_root
        )

        if md5_hash == previous_block.hash_value:
            print("Valid")
        else:
            print("Invalid")

        previous_block = current_block
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

root = Node(2, Node(1), Node(3))


def inorder(node):
    if node is None:
        return []
    return inorder(node.left) + [node.value] + inorder(node.right)

print(inorder(root))


import heapq

numbers = [5, 1, 8, 3, 9]
print("最小两个：", heapq.nsmallest(2, numbers))
print("最大两个：", heapq.nlargest(2, numbers))

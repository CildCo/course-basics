import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import json
from collections import deque
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)


class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right


def build_tree(values):
    if not values or values[0] is None:
        return None
    root = Node(values[0])
    queue = deque([root])
    index = 1
    while queue and index < len(values):
        node = queue.popleft()
        if index < len(values):
            value = values[index]
            index += 1
            if value is not None:
                node.left = Node(value)
                queue.append(node.left)
        if index < len(values):
            value = values[index]
            index += 1
            if value is not None:
                node.right = Node(value)
                queue.append(node.right)
    return root


def preorder(node):
    if node is None:
        return []
    return [node.value] + preorder(node.left) + preorder(node.right)


def inorder(node):
    if node is None:
        return []
    return inorder(node.left) + [node.value] + inorder(node.right)


data = json.loads(data_path("trees.json").read_text(encoding="utf-8"))
tree = build_tree(data["balanced"])
print("数据目录:", data_path("trees.json").parent.name)
print("层序输入:", data["balanced"])
print("前序:", preorder(tree))
print("中序:", inorder(tree))


def max_depth_brute(root):
    if root is None:
        return 0, []
    best = 0
    longest = []
    stack = [(root, [root.value])]
    while stack:
        node, path = stack.pop()
        if node.left is None and node.right is None:
            if len(path) > best:
                best = len(path)
                longest = path
        if node.left is not None:
            stack.append((node.left, path + [node.left.value]))
        if node.right is not None:
            stack.append((node.right, path + [node.right.value]))
    return best, longest


def max_depth(root):
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))


layers = {
    "空树": [],
    "单节点": data["single"],
    "链": data["skewed"],
    "平衡": data["balanced"],
}
for label, values in layers.items():
    root = build_tree(values)
    slow, path = max_depth_brute(root)
    fast = max_depth(root)
    print(f"{label:<6} 暴力 {slow}（最长路径 {path}），递归 {fast}，一致={slow == fast}")


def is_bst_brute(root):
    def collect(node):
        if node is None:
            return []
        return collect(node.left) + [node.value] + collect(node.right)

    values = collect(root)
    return all(values[index] < values[index + 1] for index in range(len(values) - 1))


def is_bst(root, low=float("-inf"), high=float("inf")):
    if root is None:
        return True
    if not (low < root.value < high):
        return False
    return is_bst(root.left, low, root.value) and is_bst(root.right, root.value, high)


cases = {
    "空树": [],
    "单节点": data["single"],
    "合法": data["bst_ok"],
    "深层违规": data["bst_bad"],
    "重复值": data["bst_dup"],
}
for label, values in cases.items():
    root = build_tree(values)
    slow = is_bst_brute(root)
    fast = is_bst(root)
    print(f"{label:<8} 中序检查 {slow!s:<5} 上下界 {fast!s:<5} 一致={slow == fast}")


def find_path(root, target):
    if root is None:
        return []
    if root.value == target:
        return [root]
    for child in (root.left, root.right):
        path = find_path(child, target)
        if path:
            return [root] + path
    return []


def lca_brute(root, first, second):
    path_first = find_path(root, first)
    path_second = find_path(root, second)
    if not path_first or not path_second:
        return None
    answer = None
    for left, right in zip(path_first, path_second):
        if left is right:
            answer = left
        else:
            break
    return answer.value if answer else None


def contains(root, target):
    if root is None:
        return False
    if root.value == target:
        return True
    return contains(root.left, target) or contains(root.right, target)


def lca(root, first, second):
    if not contains(root, first) or not contains(root, second):
        return None

    def search(node):
        if node is None or node.value == first or node.value == second:
            return node
        left = search(node.left)
        right = search(node.right)
        if left is not None and right is not None:
            return node
        return left if left is not None else right

    return search(root)


tree = build_tree(data["lca"]["tree"])
pairs = [(7, 4), (7, 8), (5, 5), (6, 4), (99, 4)]
print("查询对（含一个不存在的值）:")
for first, second in pairs:
    slow = lca_brute(tree, first, second)
    fast = lca(tree, first, second)
    fast_value = fast.value if fast is not None else None
    print(f"{first:>2} 和 {second:>2}: 路径法 {str(slow):<4}，递归 {str(fast_value):<4}，一致={slow == fast_value}")

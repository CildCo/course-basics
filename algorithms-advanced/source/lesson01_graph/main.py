from collections import defaultdict

edges = [
    ("A", "B"), ("A", "C"), ("B", "D"),
    ("C", "D"), ("D", "E"), ("E", "F"), ("C", "F"),
]

graph = defaultdict(list)
for left, right in edges:
    graph[left].append(right)
    graph[right].append(left)

for node in sorted(graph):
    print(node, "->", sorted(graph[node]))


nodes = sorted(graph)
index = {node: position for position, node in enumerate(nodes)}
matrix = [[0] * len(nodes) for _ in nodes]

for left, right in edges:
    row, column = index[left], index[right]
    matrix[row][column] = 1
    matrix[column][row] = 1

print("    " + " ".join(nodes))
for node, row in zip(nodes, matrix):
    print(node, " ", " ".join(str(value) for value in row))


print("节点数:", len(nodes))
print("边数:", len(edges))
for node in nodes:
    print(f"{node} 的度: {len(graph[node])}")

print("邻接表：空间 O(V+E)，遍历邻居 O(degree)，判断两点相连 O(degree)")
print("邻接矩阵：空间 O(V^2)，遍历邻居 O(V)，判断两点相连 O(1)")

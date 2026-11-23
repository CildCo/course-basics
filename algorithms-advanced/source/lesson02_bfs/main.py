from collections import deque

graph = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D", "F"],
    "D": ["B", "C", "E"],
    "E": ["D", "F"],
    "F": ["C", "E"],
    "G": [],
}


def bfs(start):
    distance = {start: 0}
    parent = {start: None}
    queue = deque([start])

    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in distance:
                distance[neighbor] = distance[node] + 1
                parent[neighbor] = node
                queue.append(neighbor)

    return distance, parent

distance, parent = bfs("A")
for node in sorted(distance):
    print(f"A -> {node}: 距离 {distance[node]}")
print("无法到达的节点:", sorted(set(graph) - set(distance)))


def build_path(parent, end):
    path = []
    while end is not None:
        path.append(end)
        end = parent[end]
    return path[::-1]

print("A 到 F 的路径:", " -> ".join(build_path(parent, "F")))
print("A 到 F 的边数:", distance["F"])
print("A 到 E 的路径:", " -> ".join(build_path(parent, "E")))


for target in ["F", "E", "G"]:
    if target in distance:
        print(f"A -> {target}: {distance[target]} 条边，路径 {' -> '.join(build_path(parent, target))}")
    else:
        print(f"A -> {target}: 不可达")

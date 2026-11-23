import heapq

graph = {
    "A": {"B": 4, "C": 2},
    "B": {"A": 4, "C": 1, "D": 5},
    "C": {"A": 2, "B": 1, "D": 8, "E": 10},
    "D": {"B": 5, "C": 8, "E": 2, "F": 6},
    "E": {"C": 10, "D": 2, "F": 3},
    "F": {"D": 6, "E": 3},
}


def dijkstra(graph, start):
    distance = {node: float("inf") for node in graph}
    distance[start] = 0
    parent = {start: None}
    heap = [(0, start)]

    while heap:
        current_distance, node = heapq.heappop(heap)
        if current_distance > distance[node]:
            continue
        for neighbor, weight in graph[node].items():
            candidate = current_distance + weight
            if candidate < distance[neighbor]:
                distance[neighbor] = candidate
                parent[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))

    return distance, parent

distance, parent = dijkstra(graph, "A")
for node in sorted(distance):
    print(f"A -> {node}: {distance[node]}")


def build_path(parent, end):
    path = []
    while end is not None:
        path.append(end)
        end = parent[end]
    return path[::-1]

path = build_path(parent, "F")
print("A 到 F 的最短路径:", " -> ".join(path))
print("总距离:", distance["F"])
print("经过的节点数:", len(path))


from collections import deque

def bfs_hops(graph, start, end):
    queue = deque([start])
    parent = {start: None}
    while queue:
        node = queue.popleft()
        if node == end:
            break
        for neighbor in graph[node]:
            if neighbor not in parent:
                parent[neighbor] = node
                queue.append(neighbor)
    if end not in parent:
        return None
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = parent[current]
    return path[::-1]

bfs_path = bfs_hops(graph, "A", "F")
print("BFS 跳数最少的路径:", " -> ".join(bfs_path), "（", len(bfs_path) - 1, "条边）")
print("Dijkstra 最短距离路径:", " -> ".join(path), "（总距离", distance["F"], "）")


reachable = sorted((node for node in distance if distance[node] < float("inf")), key=lambda node: distance[node])
print("按距离从近到远:")
for node in reachable:
    print(f"  {node}: {distance[node]}")

graph = {
    "A": ["B"],
    "B": ["A", "C"],
    "C": ["B"],
    "D": ["E", "F"],
    "E": ["D"],
    "F": ["D", "G"],
    "G": ["F"],
    "H": [],
}

print("节点数:", len(graph))
print("边数:", sum(len(neighbors) for neighbors in graph.values()) // 2)


def dfs_recursive(node, unseen, component):
    unseen.remove(node)
    component.append(node)
    for neighbor in graph[node]:
        if neighbor in unseen:
            dfs_recursive(neighbor, unseen, component)

unseen = set(graph)
component = []
dfs_recursive("A", unseen, component)
print("从 A 出发访问到的节点:", component)
print("剩余未访问节点:", sorted(unseen))


def dfs_iterative(start, unseen):
    stack = [start]
    unseen.discard(start)
    component = []

    while stack:
        node = stack.pop()
        component.append(node)
        for neighbor in reversed(graph[node]):
            if neighbor in unseen:
                unseen.discard(neighbor)
                stack.append(neighbor)

    return component

unseen = set(graph)
print("迭代 DFS 从 D 出发:", dfs_iterative("D", unseen))


unseen = set(graph)
components = []
while unseen:
    start = min(unseen)
    component = []
    dfs_recursive(start, unseen, component)
    components.append(component)

for index, component in enumerate(components, 1):
    print(f"分量 {index}: {component}（{len(component)} 个节点）")

largest = max(components, key=len)
print("最大连通分量:", largest)

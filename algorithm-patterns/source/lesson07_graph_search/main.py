import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import json
from collections import defaultdict, deque
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
graph_data = json.loads(data_path("graph.json").read_text(encoding="utf-8"))
print("数据目录:", data_path("graph.json").parent.name)
print("节点对:", graph_data["edges"])
print("起点和终点:", graph_data["start"], "->", graph_data["goal"])


def build_undirected(edges):
    graph = defaultdict(list)
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    return graph


def all_simple_paths(graph, start, goal):
    paths = []

    def dfs(node, path, visited):
        if node == goal:
            paths.append(path[:])
            return
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)

    dfs(start, [start], {start})
    return paths


def shortest_path(graph, start, goal):
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        if node == goal:
            return path
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return []


graph = build_undirected(graph_data["edges"])
start, goal = graph_data["start"], graph_data["goal"]
paths = all_simple_paths(graph, start, goal)
shortest = min(paths, key=len) if paths else []
print("DFS 找到的路径数:", len(paths))
print("其中一条较长路径:", max(paths, key=len) if paths else [])
print("最短路径:", shortest, "长度:", len(shortest) - 1)
print("BFS 结果:", shortest_path(graph, start, goal))


cases = [
    ({"A": ["B"], "B": ["A"], "C": ["D"], "D": ["C"]}, "A", "D"),
    ({"A": ["B", "C"], "B": ["A"], "C": ["A"]}, "A", "A"),
    ({"A": ["B"], "B": ["A"]}, "A", "Z"),
]
print("不可达、起点等于终点、终点不存在:")
for case_graph, case_start, case_goal in cases:
    print(f"{case_start}->{case_goal}: {shortest_path(case_graph, case_start, case_goal)}")


def has_cycle_brute(nodes, edges):
    index = {node: position for position, node in enumerate(nodes)}
    size = len(nodes)
    reach = [[False] * size for _ in range(size)]
    for left, right in edges:
        if left in index and right in index:
            reach[index[left]][index[right]] = True
    for middle in range(size):
        for source in range(size):
            if not reach[source][middle]:
                continue
            for target in range(size):
                if reach[middle][target]:
                    reach[source][target] = True
    return any(reach[position][position] for position in range(size))


def has_cycle_kahn(nodes, edges):
    graph = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for left, right in edges:
        graph.setdefault(left, []).append(right)
        indegree.setdefault(left, 0)
        indegree[right] = indegree.get(right, 0) + 1
    queue = deque([node for node, degree in indegree.items() if degree == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in graph.get(node, []):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    return visited != len(indegree)


courses = json.loads(data_path("courses.json").read_text(encoding="utf-8"))
for label in ["acyclic", "cyclic"]:
    edges = courses[label]
    nodes = sorted({node for edge in edges for node in edge})
    print(f"{label}: 传递闭包 {has_cycle_brute(nodes, edges)}，拓扑排序 {has_cycle_kahn(nodes, edges)}")


cases = [
    ("空图", [], []),
    ("单节点", ["A"], []),
    ("自环", ["A"], [["A", "A"]]),
    ("两个子图", ["A", "B", "C", "D"], [["A", "B"], ["C", "D"]]),
    ("环", ["A", "B", "C"], [["A", "B"], ["B", "C"], ["C", "A"]]),
]
print(f"{'场景':<10}{'传递闭包':<10}{'拓扑排序':<10}{'一致'}")
for label, nodes, edges in cases:
    slow = has_cycle_brute(nodes, edges)
    fast = has_cycle_kahn(nodes, edges)
    print(f"{label:<10}{str(slow):<10}{str(fast):<10}{slow == fast}")


def neighbors(grid, row, column):
    rows, cols = len(grid), len(grid[0])
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        next_row, next_col = row + dr, column + dc
        if 0 <= next_row < rows and 0 <= next_col < cols:
            yield next_row, next_col


def component_cells(grid, start, seen):
    stack = [start]
    seen.add(start)
    cells = []
    while stack:
        row, column = stack.pop()
        cells.append((row, column))
        for next_row, next_col in neighbors(grid, row, column):
            if grid[next_row][next_col] == 1 and (next_row, next_col) not in seen:
                seen.add((next_row, next_col))
                stack.append((next_row, next_col))
    return cells


def count_islands_brute(grid):
    if not grid:
        return 0
    count = 0
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            if grid[row][column] == 1:
                cells = component_cells(grid, (row, column), set())
                if (row, column) == min(cells):
                    count += 1
    return count


def count_islands(grid):
    if not grid:
        return 0
    seen = set()
    count = 0
    for row in range(len(grid)):
        for column in range(len(grid[0])):
            if grid[row][column] == 1 and (row, column) not in seen:
                component_cells(grid, (row, column), seen)
                count += 1
    return count


grid = [[int(char) for char in line.strip()] for line in data_path("grid.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
print("网格:")
for line in grid:
    print(" ".join(str(value) for value in line))
print("暴力:", count_islands_brute(grid))
print("全局 visited:", count_islands(grid))


cases = [
    ("空网格", []),
    ("全水", [[0, 0], [0, 0]]),
    ("单格", [[1]]),
    ("对角", [[1, 0], [0, 1]]),
    ("全陆地", [[1, 1], [1, 1]]),
]
for label, case in cases:
    slow = count_islands_brute(case)
    fast = count_islands(case)
    print(f"{label:<8} 暴力 {slow}，优化 {fast}，一致={slow == fast}")


def bfs_layers(grid, start):
    seen = {start}
    frontier = [start]
    layers = []
    depth = 0
    while frontier:
        layers.append((depth, list(frontier)))
        next_frontier = []
        for row, column in frontier:
            for next_row, next_col in neighbors(grid, row, column):
                if grid[next_row][next_col] == 1 and (next_row, next_col) not in seen:
                    seen.add((next_row, next_col))
                    next_frontier.append((next_row, next_col))
        frontier = next_frontier
        depth += 1
    return layers


seen = set()
largest = []
for row in range(len(grid)):
    for column in range(len(grid[0])):
        if grid[row][column] == 1 and (row, column) not in seen:
            cells = component_cells(grid, (row, column), seen)
            if len(cells) > len(largest):
                largest = cells
start = min(largest)
layers = bfs_layers(grid, start)
layer_map = [[-1] * len(grid[0]) for _ in grid]
for depth, cells in layers:
    for row, column in cells:
        layer_map[row][column] = depth

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
axes[0].imshow(grid, cmap="Greys", vmin=0, vmax=1)
axes[0].set_title("岛屿网格（黑色为陆地）")
axes[1].imshow(grid, cmap="Greys", vmin=0, vmax=1, alpha=0.35)
for row in range(len(grid)):
    for column in range(len(grid[0])):
        if layer_map[row][column] >= 0:
            axes[1].text(column, row, str(layer_map[row][column]), ha="center", va="center", color="#B23A48", fontsize=9, fontweight="bold")
axes[1].set_title("最大岛屿的 BFS 层号")
for ax in axes:
    ax.set_xticks(range(len(grid[0])))
    ax.set_yticks(range(len(grid)))
    ax.grid(color="#CBD5E1", linewidth=0.8)
fig.tight_layout()
fig.savefig(out / "island_bfs.png", dpi=130, bbox_inches="tight")
plt.close(fig)

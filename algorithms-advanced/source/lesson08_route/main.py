import heapq
from pathlib import Path

# 每条边是 (距离 km, 平均速度 km/h)
graph = {
    "火车站": {"市中心": (4, 30), "大学城": (7, 35)},
    "市中心": {"火车站": (4, 30), "图书馆": (3, 25), "公园": (5, 30), "大学城": (6, 28)},
    "图书馆": {"市中心": (3, 25), "公园": (2, 20), "科技园": (6, 35)},
    "公园": {"市中心": (5, 30), "图书馆": (2, 20), "科技园": (4, 30), "体育馆": (7, 28)},
    "大学城": {"火车站": (7, 35), "市中心": (6, 28), "科技园": (5, 32), "体育馆": (3, 25)},
    "科技园": {"图书馆": (6, 35), "公园": (4, 30), "大学城": (5, 32), "体育馆": (2, 30)},
    "体育馆": {"大学城": (3, 25), "科技园": (2, 30), "公园": (7, 28)},
}
print("地点数:", len(graph))
print("道路数:", sum(len(edges) for edges in graph.values()) // 2)


def dijkstra(graph, start):
    distance = {node: float("inf") for node in graph}
    distance[start] = 0
    parent = {start: None}
    heap = [(0, start)]

    while heap:
        current, node = heapq.heappop(heap)
        if current > distance[node]:
            continue
        for neighbor, (length, speed) in graph[node].items():
            candidate = current + length
            if candidate < distance[neighbor]:
                distance[neighbor] = candidate
                parent[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))

    return distance, parent

def build_route(graph, parent, end):
    nodes = []
    current = end
    while current is not None:
        nodes.append(current)
        current = parent[current]
    nodes.reverse()

    total_distance = 0.0
    total_minutes = 0.0
    for left, right in zip(nodes, nodes[1:]):
        length, speed = graph[left][right]
        total_distance += length
        total_minutes += length / speed * 60
    return nodes, total_distance, total_minutes

distance, parent = dijkstra(graph, "火车站")
routes, total_distance, total_minutes = build_route(graph, parent, "科技园")
print("路径:", " -> ".join(routes))
print("总距离:", total_distance, "km")
print("预计时间:", round(total_minutes, 1), "分钟")


queries = [
    ("火车站", "科技园"),
    ("大学城", "图书馆"),
    ("体育馆", "火车站"),
    ("公园", "大学城"),
]

rows = []
for start, end in queries:
    distances, parents = dijkstra(graph, start)
    route, length, minutes = build_route(graph, parents, end)
    rows.append((start, end, " -> ".join(route), length, round(minutes, 1)))

print(f"{'起点':<5}{'终点':<5}{'距离':>6}{'时间':>8}  路径")
for start, end, route, length, minutes in rows:
    print(f"{start:<5}{end:<5}{length:>6.1f}{minutes:>7.1f}分  {route}")


output_dir = Path.cwd() / "output"
output_dir.mkdir(exist_ok=True)

lines = ["# 城市路线规划报告", "", "## 查询结果", ""]
lines.append("| 起点 | 终点 | 距离 (km) | 预计时间 (分钟) | 路径 |")
lines.append("| --- | --- | ---: | ---: | --- |")
for start, end, route, length, minutes in rows:
    lines.append(f"| {start} | {end} | {length:.1f} | {minutes:.1f} | {route} |")

lines.extend([
    "",
    "## 说明",
    "",
    "- 距离按道路长度累计，时间为距离除以平均速度。",
    "- 模型不考虑红绿灯、拥堵和临时封路。",
    "- 所有查询使用 Dijkstra，边权必须非负。",
])
report = "\n".join(lines) + "\n"
(output_dir / "route-report.md").write_text(report, encoding="utf-8")
print(report)

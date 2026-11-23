items = [
    ("水", 3, 10),
    ("帐篷", 5, 25),
    ("相机", 2, 15),
    ("食物", 4, 20),
    ("地图", 1, 5),
]
capacity = 8

for name, weight, value in items:
    print(f"{name}: 重量 {weight}, 价值 {value}")


count = len(items)
dp = [[0] * (capacity + 1) for _ in range(count + 1)]

for index in range(1, count + 1):
    name, weight, value = items[index - 1]
    for room in range(capacity + 1):
        dp[index][room] = dp[index - 1][room]
        if room >= weight:
            dp[index][room] = max(dp[index][room], dp[index - 1][room - weight] + value)

print("      " + " ".join(f"{room:3d}" for room in range(capacity + 1)))
for index in range(count + 1):
    label = "空" if index == 0 else items[index - 1][0]
    print(f"{label:<4}" + " ".join(f"{dp[index][room]:3d}" for room in range(capacity + 1)))

print("最大价值:", dp[count][capacity])


chosen = []
remaining = capacity
for index in range(count, 0, -1):
    if dp[index][remaining] != dp[index - 1][remaining]:
        name, weight, value = items[index - 1]
        chosen.append((name, weight, value))
        remaining -= weight

chosen.reverse()
print("选中的物品:")
for name, weight, value in chosen:
    print(f"  {name}: 重量 {weight}, 价值 {value}")
print("总重量:", capacity - remaining)
print("总价值:", dp[count][capacity])


grid = [
    [1, 3, 1, 2],
    [1, 5, 1, 3],
    [4, 2, 1, 1],
    [2, 3, 2, 1],
]

rows, columns = len(grid), len(grid[0])
cost = [[0] * columns for _ in range(rows)]
cost[0][0] = grid[0][0]

for row in range(rows):
    for column in range(columns):
        if row == 0 and column == 0:
            continue
        up = cost[row - 1][column] if row > 0 else float("inf")
        left = cost[row][column - 1] if column > 0 else float("inf")
        cost[row][column] = grid[row][column] + min(up, left)

print("最小路径和表:")
for row in cost:
    print(" ".join(f"{value:3d}" for value in row))
print("从左上到右下的最小路径和:", cost[rows - 1][columns - 1])

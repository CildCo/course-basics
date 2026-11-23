import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import time
from dataclasses import dataclass, field
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
bonus = [int(value) for value in data_path("bonus.txt").read_text(encoding="utf-8").split()]
print("数据目录:", data_path("bonus.txt").parent.name)
print("每日补贴:", bonus)


def rob_brute(values):
    def dfs(index):
        if index >= len(values):
            return 0
        return max(dfs(index + 1), values[index] + dfs(index + 2))

    return dfs(0)


def rob_memo(values):
    memo = {}

    def dfs(index):
        if index >= len(values):
            return 0
        if index in memo:
            return memo[index]
        memo[index] = max(dfs(index + 1), values[index] + dfs(index + 2))
        return memo[index]

    return dfs(0)


def rob_dp(values):
    take, skip = 0, 0
    for value in values:
        take, skip = skip + value, max(skip, take)
    return max(take, skip)


cases = [[], [5], [5, 10], [2, 7, 9, 3, 1], [0, 0, 0], bonus]
print(f"{'输入':<34}{'暴力':<8}{'记忆化':<8}{'滚动':<8}{'一致'}")
for case in cases:
    slow = rob_brute(case)
    memo = rob_memo(case)
    fast = rob_dp(case)
    print(f"{str(case):<34}{slow:<8}{memo:<8}{fast:<8}{slow == memo == fast}")


@dataclass
class MockClock:
    limit_minutes: float = 45.0
    start: float = field(default_factory=time.perf_counter)
    marks: list = field(default_factory=list)

    def mark(self, label):
        elapsed = (time.perf_counter() - self.start) / 60
        self.marks.append((label, elapsed))
        print(f"[{elapsed:5.2f} 分钟] {label}")
        return elapsed

    def remaining(self):
        elapsed = (time.perf_counter() - self.start) / 60
        return max(0.0, self.limit_minutes - elapsed)


clock = MockClock()
print("限时:", clock.limit_minutes, "分钟")
print("剩余:", round(clock.remaining(), 2), "分钟")


import bisect


def lis_brute(nums):
    size = len(nums)
    best = 0
    for mask in range(1 << size):
        sequence = [nums[index] for index in range(size) if mask >> index & 1]
        if all(sequence[index] < sequence[index + 1] for index in range(len(sequence) - 1)):
            best = max(best, len(sequence))
    return best


def lis_dp(nums):
    if not nums:
        return 0
    dp = [1] * len(nums)
    for index in range(len(nums)):
        for previous in range(index):
            if nums[previous] < nums[index]:
                dp[index] = max(dp[index], dp[previous] + 1)
    return max(dp)


def lis_fast(nums):
    tails = []
    for value in nums:
        position = bisect.bisect_left(tails, value)
        if position == len(tails):
            tails.append(value)
        else:
            tails[position] = value
    return len(tails)


cases = [[10, 9, 2, 5, 3, 7, 101, 18], [1, 2, 3], [5, 5, 5], [3, 1, 2], []]
print(f"{'输入':<34}{'暴力':<8}{'O(n^2)':<8}{'O(n log n)':<12}{'一致'}")
for case in cases:
    slow = lis_brute(case)
    middle = lis_dp(case)
    fast = lis_fast(case)
    print(f"{str(case):<34}{slow:<8}{middle:<8}{fast:<12}{slow == middle == fast}")


def coin_change_brute(coins, amount):
    if amount == 0:
        return 0
    best = [float("inf")]

    def dfs(rest, count):
        if rest == 0:
            best[0] = min(best[0], count)
            return
        if rest < 0 or count >= best[0]:
            return
        for coin in coins:
            dfs(rest - coin, count + 1)

    dfs(amount, 0)
    return -1 if best[0] == float("inf") else best[0]


def coin_change(coins, amount):
    if amount < 0:
        return -1
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for value in range(1, amount + 1):
        for coin in coins:
            if value >= coin:
                dp[value] = min(dp[value], dp[value - coin] + 1)
    return -1 if dp[amount] == float("inf") else dp[amount]


cases = [([1, 2, 5], 11), ([2], 3), ([5], 5), ([], 0), ([1], 0), ([3, 7], 5)]
print(f"{'硬币':<14}{'金额':<6}{'暴力':<8}{'动态规划':<10}{'一致'}")
for coins, amount in cases:
    slow = coin_change_brute(coins, amount)
    fast = coin_change(coins, amount)
    print(f"{str(coins):<14}{amount:<6}{slow:<8}{fast:<10}{slow == fast}")


clock.mark("两道题完成")
checks = [
    ("Q1 示例", lis_fast([10, 9, 2, 5, 3, 7, 101, 18]) == 4),
    ("Q1 递增", lis_fast([1, 2, 3]) == 3),
    ("Q1 重复", lis_fast([5, 5, 5]) == 1),
    ("Q2 示例", coin_change([1, 2, 5], 11) == 3),
    ("Q2 无解", coin_change([2], 3) == -1),
    ("Q2 边界", coin_change([], 0) == 0),
]
correctness = sum(1 for _, passed in checks if passed)
complexity_points = 2 if correctness == len(checks) else 1
boundary_points = 1 if correctness == len(checks) else 0
communication_points = 1
total = correctness + complexity_points + boundary_points + communication_points
print("检查项:")
for label, passed in checks:
    print(f"  {label}: {'通过' if passed else '未通过'}")
print(f"正确性 {correctness}/6，复杂度 {complexity_points}/2，边界 {boundary_points}/1，表达 {communication_points}/1")
print(f"总分: {total}/10")
report = [
    "综合练习记录",
    "限时: 45 分钟",
    f"完成用时: {clock.marks[-1][1]:.2f} 分钟（流程演示）",
    f"正确性: {correctness}/6",
    f"复杂度说明: {complexity_points}/2",
    f"边界测试: {boundary_points}/1",
    f"表达与检查: {communication_points}/1",
    f"总分: {total}/10",
]
(out / "practice_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
print("已写入:", (out / "practice_report.txt").name)

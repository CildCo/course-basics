import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import csv
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
print("数据目录:", data_path("ledger.csv").parent.name)
print("输出目录:", out.name)


def two_sum_brute(nums, target):
    for left in range(len(nums)):
        for right in range(left + 1, len(nums)):
            if nums[left] + nums[right] == target:
                return [left, right]
    return []


def two_sum_hash(nums, target):
    seen = {}
    for index, value in enumerate(nums):
        need = target - value
        if need in seen:
            return [seen[need], index]
        seen[value] = index
    return []


cases = [([2, 7, 11, 15], 9), ([3, 3], 6), ([1, 2], 7)]
for values, goal in cases:
    print(f"{str(values):<18} 目标 {goal}: 暴力 {two_sum_brute(values, goal)}，哈希 {two_sum_hash(values, goal)}")


def longest_consecutive_sorted(nums):
    if not nums:
        return 0
    ordered = sorted(set(nums))
    best = current = 1
    for index in range(1, len(ordered)):
        if ordered[index] == ordered[index - 1] + 1:
            current += 1
        else:
            current = 1
        best = max(best, current)
    return best


def longest_consecutive(nums):
    values = set(nums)
    best = 0
    for value in values:
        if value - 1 in values:
            continue
        current = value
        length = 1
        while current + 1 in values:
            current += 1
            length += 1
        best = max(best, length)
    return best


cases = [[], [1], [1, 2, 0, 1], [100, 4, 200, 1, 3, 2], [-2, -1, 0, 1], [5, 5, 5]]
print(f"{'输入':<30}{'排序':<8}{'集合':<8}{'一致'}")
for case in cases:
    slow = longest_consecutive_sorted(case)
    fast = longest_consecutive(case)
    print(f"{str(case):<30}{slow:<8}{fast:<8}{slow == fast}")


def subarray_sum_brute(nums, target):
    count = 0
    for start in range(len(nums)):
        total = 0
        for end in range(start, len(nums)):
            total += nums[end]
            if total == target:
                count += 1
    return count


def subarray_sum_hash(nums, target):
    prefix = 0
    seen = {0: 1}
    count = 0
    for value in nums:
        prefix += value
        count += seen.get(prefix - target, 0)
        seen[prefix] = seen.get(prefix, 0) + 1
    return count


with data_path("ledger.csv").open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
amounts = [int(row["amount"]) for row in rows]
target = 5
print("每日流水:", amounts)
print("目标和:", target)
print("暴力:", subarray_sum_brute(amounts, target))
print("前缀和加哈希:", subarray_sum_hash(amounts, target))


cases = [
    ([], 0),
    ([0, 0, 0], 0),
    ([1, 1, 1], 2),
    ([1, -1, 1, -1], 0),
    ([3, 4, -1, 2, -2, 1, 5, -3, 2], 5),
    ([1, 2, 3], 100),
]
print(f"{'输入':<40}{'目标':<6}{'暴力':<8}{'哈希':<8}{'一致'}")
for values, goal in cases:
    slow = subarray_sum_brute(values, goal)
    fast = subarray_sum_hash(values, goal)
    print(f"{str(values):<40}{goal:<6}{slow:<8}{fast:<8}{slow == fast}")

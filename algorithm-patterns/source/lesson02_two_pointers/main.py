import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
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
print("数据目录:", data_path("water_levels.txt").parent.name)
print("输出目录:", out.name)


def two_sum_brute(nums, target):
    checks = 0
    for left in range(len(nums)):
        for right in range(left + 1, len(nums)):
            checks += 1
            if nums[left] + nums[right] == target:
                return (left, right), checks
    return None, checks


def two_sum_pointers(nums, target):
    left, right = 0, len(nums) - 1
    checks = 0
    while left < right:
        checks += 1
        total = nums[left] + nums[right]
        if total == target:
            return (left, right), checks
        if total < target:
            left += 1
        else:
            right -= 1
    return None, checks


nums = [-5, -3, -1, 2, 4, 7, 11]
target = 9
brute_pair, brute_checks = two_sum_brute(nums, target)
fast_pair, fast_checks = two_sum_pointers(nums, target)
print("数组:", nums, "目标:", target)
print("暴力:", brute_pair, "比较", brute_checks, "次")
print("双指针:", fast_pair, "比较", fast_checks, "次")


def check_pair(values, target, pair):
    if pair is None:
        return True
    left, right = pair
    return 0 <= left < right < len(values) and values[left] + values[right] == target


cases = [
    ([], 0),
    ([4], 8),
    ([-2, 2], 0),
    ([1, 1, 1], 2),
    ([-5, -3, -1, 2, 4, 7, 11], 9),
    ([1, 2, 3], 100),
]
print(f"{'输入':<34}{'目标':<6}{'暴力':<10}{'双指针':<10}{'一致'}")
for values, goal in cases:
    brute_pair, _ = two_sum_brute(values, goal)
    fast_pair, _ = two_sum_pointers(values, goal)
    same = (
        (brute_pair is None) == (fast_pair is None)
        and check_pair(values, goal, brute_pair)
        and check_pair(values, goal, fast_pair)
    )
    print(
        f"{str(values):<34}{goal:<6}{str(brute_pair):<10}"
        f"{str(fast_pair):<10}{same}"
    )


def remove_duplicates_brute(nums):
    result = []
    for value in nums:
        if value not in result:
            result.append(value)
    return result


def remove_duplicates(nums):
    if not nums:
        return 0
    write = 1
    for read in range(1, len(nums)):
        if nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write


samples = [[], [1], [1, 1, 1], [0, 0, 1, 1, 1, 2, 2, 3], [-2, -1, -1, 0, 1]]
for sample in samples:
    values = list(sample)
    length = remove_duplicates(values)
    print(f"{str(sample):<28} -> 新长度 {length}，内容 {values[:length]}")


def max_area_brute(heights):
    best = 0
    best_pair = None
    for left in range(len(heights)):
        for right in range(left + 1, len(heights)):
            area = min(heights[left], heights[right]) * (right - left)
            if area > best:
                best = area
                best_pair = (left, right)
    return best, best_pair


def max_area(heights):
    left, right = 0, len(heights) - 1
    best = 0
    best_pair = None
    while left < right:
        area = min(heights[left], heights[right]) * (right - left)
        if area > best:
            best = area
            best_pair = (left, right)
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return best, best_pair


heights = [int(value) for value in data_path("water_levels.txt").read_text(encoding="utf-8").split()]
print("柱子高度:", heights)
print("暴力:", max_area_brute(heights))
print("双指针:", max_area(heights))


cases = [[], [5], [0, 0], [1, 2, 3], [3, 2, 1], [4, 4, 4, 4], [1, 8, 6, 2, 5, 4, 8, 3, 7]]
print(f"{'输入':<38}{'暴力':<8}{'双指针':<8}{'一致'}")
for case in cases:
    brute, _ = max_area_brute(case)
    fast, _ = max_area(case)
    print(f"{str(case):<38}{brute:<8}{fast:<8}{brute == fast}")

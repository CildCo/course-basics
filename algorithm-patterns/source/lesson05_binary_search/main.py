import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
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
print("数据目录:", data_path("orders.txt").parent.name)
print("输出目录:", out.name)


def linear_search(nums, target):
    for index, value in enumerate(nums):
        if value == target:
            return index
    return -1


def lower_bound(nums, target):
    left, right = 0, len(nums)
    while left < right:
        mid = (left + right) // 2
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid
    return left


def upper_bound(nums, target):
    left, right = 0, len(nums)
    while left < right:
        mid = (left + right) // 2
        if nums[mid] <= target:
            left = mid + 1
        else:
            right = mid
    return left


nums = [1, 3, 5, 7, 9, 11, 13]
for target in [7, 8, 0, 20]:
    position = lower_bound(nums, target)
    found = position < len(nums) and nums[position] == target
    print(f"target={target:>2}: 线性查找 {linear_search(nums, target):>2}，lower_bound {position}，存在={found}")


cases = [([], 5), ([1], 0), ([1], 1), ([1], 2), ([1, 2, 2, 2, 4], 2), ([1, 2, 2, 2, 4], 3)]
print(f"{'输入':<22}{'目标':<6}{'lower':<7}{'upper':<7}{'次数'}")
for values, target in cases:
    low = lower_bound(values, target)
    high = upper_bound(values, target)
    print(f"{str(values):<22}{target:<6}{low:<7}{high:<7}{high - low}")


def rotated_min_brute(nums):
    return min(nums) if nums else None


def rotated_min(nums):
    if not nums:
        return None
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        elif nums[mid] < nums[right]:
            right = mid
        else:
            right -= 1
    return nums[left]


cases = [[], [3], [1, 2], [3, 1], [4, 5, 6, 7, 0, 1, 2], [1, 2, 3, 4], [2, 2, 2, 0, 2]]
print(f"{'输入':<32}{'暴力':<8}{'二分':<8}{'一致'}")
for case in cases:
    slow = rotated_min_brute(case)
    fast = rotated_min(case)
    print(f"{str(case):<32}{str(slow):<8}{str(fast):<8}{slow == fast}")


from itertools import combinations


def can_split(orders, k, limit):
    groups = 1
    current = 0
    for weight in orders:
        if weight > limit:
            return False
        if current + weight > limit:
            groups += 1
            current = weight
        else:
            current += weight
    return groups <= k


def split_brute(orders, k):
    n = len(orders)
    if k <= 0 or k > n:
        return None
    if k == 1:
        return sum(orders)
    best = float("inf")
    for cuts in combinations(range(1, n), k - 1):
        positions = (0,) + cuts + (n,)
        largest = max(sum(orders[positions[i]:positions[i + 1]]) for i in range(k))
        best = min(best, largest)
    return best


def split_fast(orders, k):
    if not orders or k <= 0 or k > len(orders):
        return None
    low, high = max(orders), sum(orders)
    while low < high:
        mid = (low + high) // 2
        if can_split(orders, k, mid):
            high = mid
        else:
            low = mid + 1
    return low


orders = [int(value) for value in data_path("orders.txt").read_text(encoding="utf-8").split()]
print("订单:", orders)
for k in [1, 2, 3, 5]:
    print(f"k={k}: 暴力 {split_brute(orders, k)}，二分 {split_fast(orders, k)}")


cases = [([], 0), ([], 1), ([5], 1), ([5], 2), ([7, 2, 5, 10, 8], 2), ([0, 0, 0], 2), ([7, 2, 5, 10, 8], 5)]
print(f"{'输入':<26}{'k':<4}{'暴力':<8}{'二分':<8}{'一致'}")
for values, k in cases:
    slow = split_brute(values, k)
    fast = split_fast(values, k)
    print(f"{str(values):<26}{k:<4}{str(slow):<8}{str(fast):<8}{slow == fast}")


def lower_bound_trace(nums, target):
    left, right = 0, len(nums)
    trace = []
    while left < right:
        mid = (left + right) // 2
        trace.append((left, right, mid))
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid
    trace.append((left, right, None))
    return trace


nums = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
target = 11
trace = lower_bound_trace(nums, target)
fig, axes = plt.subplots(len(trace), 1, figsize=(8, 1.35 * len(trace)), sharex=True)
for ax, (left, right, mid) in zip(axes, trace):
    colors = ["#D9E2EC"] * len(nums)
    for index in range(left, min(right, len(nums))):
        colors[index] = "#8FB8DE"
    if mid is not None:
        colors[mid] = "#E45756"
    ax.bar(range(len(nums)), nums, color=colors, width=0.7)
    ax.set_ylim(0, 22)
    ax.set_yticks([])
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    label = f"[{left}, {right})"
    if mid is not None:
        label += f"  mid={mid}"
    ax.set_ylabel(label, rotation=0, ha="right", va="center", fontsize=9)
axes[0].set_title(f"在有序数组中查找 {target} 的区间收缩")
axes[-1].set_xticks(range(len(nums)))
axes[-1].set_xticklabels(nums)
fig.tight_layout()
fig.savefig(out / "binary_search_steps.png", dpi=130, bbox_inches="tight")
plt.close(fig)

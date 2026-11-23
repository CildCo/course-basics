import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import json
import math
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
print("数据目录:", data_path("algorithm_patterns.json").parent.name)
print("输出目录:", out.name)


def log_steps(n):
    steps = 0
    while n > 1:
        n //= 2
        steps += 1
    return steps


def linear_steps(n):
    return n


def linearithmic_steps(n):
    return n * log_steps(n)


def quadratic_steps(n):
    return n * n


sizes = [8, 64, 512, 4096]
print(f"{'n':>6} {'O(1)':>8} {'O(log n)':>10} {'O(n)':>10} {'O(n log n)':>12} {'O(n^2)':>12}")
for n in sizes:
    print(
        f"{n:>6} {1:>8} {log_steps(n):>10} {linear_steps(n):>10} "
        f"{linearithmic_steps(n):>12} {quadratic_steps(n):>12}"
    )


n_values = list(range(1, 101))
curves = {
    "O(1)": [1 for _ in n_values],
    "O(log n)": [log_steps(n) for n in n_values],
    "O(n)": [n for n in n_values],
    "O(n log n)": [n * log_steps(n) for n in n_values],
    "O(n^2)": [n * n for n in n_values],
}
colors = ["#6B7280", "#4C78A8", "#54A24B", "#F58518", "#E45756"]
fig, ax = plt.subplots(figsize=(8.5, 4.8))
for (label, values), color in zip(curves.items(), colors):
    ax.plot(n_values, values, label=label, color=color, linewidth=2)
ax.set_yscale("log")
ax.set_xlabel("输入规模 n")
ax.set_ylabel("操作次数（对数刻度）")
ax.set_title("常见复杂度的增长差距")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, ncol=5, loc="upper left", fontsize=9)
fig.tight_layout()
fig.savefig(out / "complexity_growth.png", dpi=130, bbox_inches="tight")
plt.close(fig)


def has_duplicate_brute(values):
    comparisons = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            comparisons += 1
            if values[i] == values[j]:
                return True, comparisons
    return False, comparisons


def has_duplicate_sorted(values):
    ordered = sorted(values)
    comparisons = 0
    for i in range(1, len(ordered)):
        comparisons += 1
        if ordered[i] == ordered[i - 1]:
            return True, comparisons
    return False, comparisons


samples = [[1, 2, 3, 4], [1, 2, 3, 1], [5, 4, 3, 2, 1]]
for sample in samples:
    brute, brute_checks = has_duplicate_brute(sample)
    fast, fast_checks = has_duplicate_sorted(sample)
    print(
        f"{str(sample):<18} 暴力={brute!s:<5} 比较 {brute_checks:>2} 次   "
        f"排序={fast!s:<5} 比较 {fast_checks:>2} 次"
    )


cases = [
    [],
    [7],
    [1, 2, 3, 4],
    [1, 2, 3, 1],
    [0, 0],
    [-3, -1, -3],
    [5, 4, 3, 2, 1],
]
print(f"{'输入':<22}{'暴力':<8}{'排序':<8}{'一致'}")
for case in cases:
    brute, _ = has_duplicate_brute(case)
    fast, _ = has_duplicate_sorted(case)
    print(f"{str(case):<22}{str(brute):<8}{str(fast):<8}{brute == fast}")


patterns = json.loads(data_path("algorithm_patterns.json").read_text(encoding="utf-8"))["patterns"]
print(f"{'题面信号':<30}{'优先结构':<20}{'目标复杂度'}")
for row in patterns:
    print(f"{row['signal']:<30}{row['pattern']:<20}{row['target']}")


BUDGET = 10_000_000
print("按每秒 1000 万次基本操作估算可接受的复杂度")
for n in [10, 20, 100, 1_000, 100_000, 1_000_000]:
    allowed = ["O(1)", "O(log n)"]
    if n <= BUDGET:
        allowed.append("O(n)")
    if n * max(1, math.log2(n)) <= BUDGET:
        allowed.append("O(n log n)")
    if n * n <= BUDGET:
        allowed.append("O(n^2)")
    print(f"n={n:>8}: " + ", ".join(allowed))


checklist = [
    "1. 复述输入输出，确认空输入和单元素输入",
    "2. 用两三个小例子手算，写出预期结果",
    "3. 先说暴力解法，给出复杂度，再找瓶颈",
    "4. 用数据结构或单调性优化，说明为什么不会漏解",
    "5. 跑边界用例，检查下标、重复值和溢出",
]
text = "\n".join(checklist) + "\n"
(out / "lesson01_checklist.txt").write_text(text, encoding="utf-8")
print(text, end="")
print("已写入:", (out / "lesson01_checklist.txt").name)

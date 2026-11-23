from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from scipy import stats
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
print("课程数据目录:", data_path("ab_test_users.csv").parent.name)
print("输出目录:", out.name)


def sample_size_per_group(p1, p2, alpha=0.05, power=0.8):
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)
    pbar = (p1 + p2) / 2
    numerator = (
        z_alpha * math.sqrt(2 * pbar * (1 - pbar))
        + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    return math.ceil(numerator / (p2 - p1) ** 2)


rows = []
for target in [0.14, 0.16, 0.18, 0.19, 0.22]:
    n_needed = sample_size_per_group(0.12, target)
    rows.append([0.12, target, round(target - 0.12, 4), n_needed, n_needed * 2])

plan = pd.DataFrame(rows, columns=["基线", "目标转化率", "绝对提升", "每组样本量", "总样本量"])
display(plan)
print("计划参数：alpha=0.05，power=0.8，双侧检验")


rng = np.random.default_rng(2026)


def simulated_power(p1, p2, n, reps=1000, alpha=0.05):
    x1 = rng.binomial(n, p1, reps)
    x2 = rng.binomial(n, p2, reps)
    p1_hat = x1 / n
    p2_hat = x2 / n
    pooled = (x1 + x2) / (2 * n)
    se = np.sqrt(pooled * (1 - pooled) * 2 / n)
    z_scores = (p2_hat - p1_hat) / se
    return float(np.mean(np.abs(z_scores) > stats.norm.ppf(1 - alpha / 2)))


sizes = [200, 300, 400, 500, 600, 800, 1000]
powers = [simulated_power(0.12, 0.19, n) for n in sizes]

power_table = pd.DataFrame({"每组样本量": sizes, "模拟功效": powers})
power_table["模拟功效"] = power_table["模拟功效"].round(3)
display(power_table)


grid = list(range(100, 1250, 50))
curve = [simulated_power(0.12, 0.19, n, reps=800) for n in grid]

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(grid, curve, color="#4C78A8", linewidth=2, marker="o", markersize=3)
ax.axhline(0.8, color="#E45756", linestyle="--", linewidth=1, label="目标功效 0.8")
ax.axvline(419, color="#54A24B", linestyle=":", linewidth=1.2, label="公式估算 419 人/组")
ax.set_xlabel("每组样本量")
ax.set_ylabel("检测出 7 个百分点提升的概率")
ax.set_title("样本量与统计功效（基线 12%，目标 19%）")
ax.set_ylim(0, 1.02)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(out / "power-curve.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "power-curve.png")))
plt.close(fig)


fixed_n = 500
mde_rows = []
for target in [0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20]:
    power = simulated_power(0.12, target, fixed_n, reps=800)
    mde_rows.append([target, round(target - 0.12, 4), round(power, 3)])

mde = pd.DataFrame(mde_rows, columns=["实验组真实转化率", "绝对提升", "每组 500 人时的功效"])
display(mde)
print("样本量不足时，不要用“不显著”证明“没有效果”。")

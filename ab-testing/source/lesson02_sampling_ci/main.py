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


users = pd.read_csv(data_path("ab_test_users.csv"))
control = users[users["group"] == "control"]

n = len(control)
p = control["converted"].mean()
se = math.sqrt(p * (1 - p) / n)
z = stats.norm.ppf(0.975)
low, high = p - z * se, p + z * se

print("对照组样本量:", n)
print("样本转化率:", round(p, 4))
print("标准误:", round(se, 4))
print("95% 置信区间:", f"[{low:.4f}, {high:.4f}]")
print("区间宽度:", round(high - low, 4))


rng = np.random.default_rng(42)
true_p = 0.15
sample_size = 500
reps = 2000
covered = 0
widths = []

for _ in range(reps):
    x = rng.binomial(sample_size, true_p)
    phat = x / sample_size
    se_hat = math.sqrt(phat * (1 - phat) / sample_size)
    lo = phat - z * se_hat
    hi = phat + z * se_hat
    covered += int(lo <= true_p <= hi)
    widths.append(hi - lo)

print("模拟次数:", reps)
print("覆盖率:", round(covered / reps, 4))
print("平均区间宽度:", round(float(np.mean(widths)), 4))


rng = np.random.default_rng(7)
rows = []
for i in range(40):
    x = rng.binomial(sample_size, true_p)
    phat = x / sample_size
    se_hat = math.sqrt(phat * (1 - phat) / sample_size)
    rows.append((i + 1, phat - z * se_hat, phat + z * se_hat, phat))

fig, ax = plt.subplots(figsize=(9, 4.4))
for i, lo, hi, phat in rows:
    hit = lo <= true_p <= hi
    color = "#4C78A8" if hit else "#E45756"
    ax.plot([i, i], [lo, hi], color=color, linewidth=2)
    ax.scatter(i, phat, color=color, s=14, zorder=3)
ax.axhline(true_p, color="#333333", linestyle="--", linewidth=1, label="真实转化率")
ax.set_xlabel("第几次抽样")
ax.set_ylabel("转化率")
ax.set_title("40 次抽样的 95% 置信区间")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(out / "ci-coverage.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "ci-coverage.png")))
plt.close(fig)

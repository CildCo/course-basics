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
converted = users["converted"].to_numpy()
is_treatment = (users["group"] == "treatment").to_numpy()

rate_control = converted[~is_treatment].mean()
rate_treatment = converted[is_treatment].mean()
observed_diff = rate_treatment - rate_control

print("对照组转化率:", round(rate_control, 4))
print("实验组转化率:", round(rate_treatment, 4))
print("观察到的绝对差:", round(observed_diff, 4))


rng = np.random.default_rng(2026)
n_perm = 5000
n_treatment = int(is_treatment.sum())
perm_diffs = np.empty(n_perm)

labels = is_treatment.copy()
for i in range(n_perm):
    rng.shuffle(labels)
    treat = converted[labels]
    ctrl = converted[~labels]
    perm_diffs[i] = treat.mean() - ctrl.mean()

p_value = (np.sum(np.abs(perm_diffs) >= abs(observed_diff)) + 1) / (n_perm + 1)
print("置换次数:", n_perm)
print("零假设下差距的均值:", round(float(perm_diffs.mean()), 4))
print("零假设下差距的标准差:", round(float(perm_diffs.std(ddof=1)), 4))
print("置换检验 p 值:", round(float(p_value), 4))


fig, ax = plt.subplots(figsize=(9, 4.4))
ax.hist(perm_diffs, bins=45, color="#A8C4DC", edgecolor="white", linewidth=0.4)
ax.axvline(observed_diff, color="#E45756", linewidth=2, label="观察到的差距")
ax.axvline(-observed_diff, color="#E45756", linewidth=1, linestyle="--", alpha=0.6)
ax.set_xlabel("实验组减对照组的转化率差")
ax.set_ylabel("出现次数")
ax.set_title("零假设下的置换分布")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(out / "permutation-null.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "permutation-null.png")))
plt.close(fig)


n1 = int((~is_treatment).sum())
n2 = int(is_treatment.sum())
x1 = int(converted[~is_treatment].sum())
x2 = int(converted[is_treatment].sum())
p1 = x1 / n1
p2 = x2 / n2
pooled = (x1 + x2) / (n1 + n2)
se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
z_score = (p2 - p1) / se_pooled
p_normal = 2 * stats.norm.sf(abs(z_score))

print("z 值:", round(z_score, 4))
print("正态近似 p 值:", round(float(p_normal), 4))
print("两种方法结论是否一致:", (p_value < 0.05) == (p_normal < 0.05))

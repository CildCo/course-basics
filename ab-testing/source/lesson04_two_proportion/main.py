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
table = pd.crosstab(users["group"], users["converted"])
table.columns = ["未转化", "转化"]
display(table)

control = users[users["group"] == "control"]
treatment = users[users["group"] == "treatment"]
n1, x1 = len(control), int(control["converted"].sum())
n2, x2 = len(treatment), int(treatment["converted"].sum())

print("对照组: 转化", x1, "/", n1, "=", round(x1 / n1, 4))
print("实验组: 转化", x2, "/", n2, "=", round(x2 / n2, 4))


def two_proportion_test(x1, n1, x2, n2, alpha=0.05):
    p1 = x1 / n1
    p2 = x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    diff = p2 - p1
    z_score = diff / se_pooled
    p_value = 2 * stats.norm.sf(abs(z_score))

    se_unpooled = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_low = diff - z_crit * se_unpooled
    ci_high = diff + z_crit * se_unpooled

    return {
        "p1": p1,
        "p2": p2,
        "diff": diff,
        "relative_lift": diff / p1,
        "z": z_score,
        "p_value": p_value,
        "ci_low": ci_low,
        "ci_high": ci_high,
    }


result = two_proportion_test(x1, n1, x2, n2)
for key in ["p1", "p2", "diff", "relative_lift", "z", "p_value", "ci_low", "ci_high"]:
    value = result[key]
    if key in {"p1", "p2", "diff", "p_value", "ci_low", "ci_high"}:
        print(f"{key}: {value:.4f}")
    elif key == "relative_lift":
        print(f"{key}: {value:.2%}")
    else:
        print(f"{key}: {value:.4f}")


contingency = np.array([[x1, n1 - x1], [x2, n2 - x2]])
chi2, p_chi2, dof, expected = stats.chi2_contingency(contingency, correction=False)

print("2x2 列联表:")
print(contingency)
print()
print("卡方值:", round(float(chi2), 4))
print("卡方检验 p 值:", round(float(p_chi2), 4))
print("z 值的平方:", round(float(result["z"] ** 2), 4))
print("手工 z 检验 p 值:", round(float(result["p_value"]), 4))

if result["p_value"] < 0.05 and result["ci_low"] > 0:
    print("结论：在 5% 显著水平下，实验组转化率更高，且提升区间不包含 0。")
else:
    print("结论：证据不足以认为两组转化率不同。")

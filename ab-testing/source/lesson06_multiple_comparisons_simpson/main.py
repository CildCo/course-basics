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
treatment = users[users["group"] == "treatment"]


def prop_test_p(x1, n1, x2, n2):
    p1 = x1 / n1
    p2 = x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z_score = (p2 - p1) / se
    return 2 * stats.norm.sf(abs(z_score))


metrics = []
metrics.append([
    "注册转化率",
    prop_test_p(int(control["converted"].sum()), len(control), int(treatment["converted"].sum()), len(treatment)),
    "主指标",
])
metrics.append([
    "7 日留存率",
    prop_test_p(int(control["retained_7d"].sum()), len(control), int(treatment["retained_7d"].sum()), len(treatment)),
    "护栏指标",
])
session_test = stats.ttest_ind(control["session_seconds"], treatment["session_seconds"], equal_var=False)
metrics.append(["人均时长", float(session_test.pvalue), "辅助指标"])

metric_table = pd.DataFrame(metrics, columns=["指标", "原始 p 值", "角色"])
metric_table["原始 p 值"] = metric_table["原始 p 值"].round(4)
metric_table["Bonferroni 门槛"] = round(0.05 / len(metric_table), 4)
metric_table["是否通过 Bonferroni"] = metric_table["原始 p 值"] < 0.05 / len(metric_table)
display(metric_table)


rng = np.random.default_rng(11)


def family_wise_error(m, reps=1000):
    any_uncorrected = 0
    any_bonferroni = 0
    threshold = 0.05 / m
    for _ in range(reps):
        p_values = []
        for _ in range(m):
            x1 = rng.binomial(500, 0.15)
            x2 = rng.binomial(500, 0.15)
            p_values.append(prop_test_p(x1, 500, x2, 500))
        if min(p_values) < 0.05:
            any_uncorrected += 1
        if min(p_values) < threshold:
            any_bonferroni += 1
    return any_uncorrected / reps, any_bonferroni / reps


rows = []
for m in [1, 3, 10]:
    raw, corrected = family_wise_error(m, reps=800)
    rows.append([m, round(raw, 3), round(corrected, 3)])

error_table = pd.DataFrame(rows, columns=["检验个数", "不校正的假阳性率", "Bonferroni 后假阳性率"])
display(error_table)


simpson = pd.read_csv(data_path("simpson_segments.csv"))

overall = simpson.groupby("group")["converted"].agg(["count", "sum", "mean"]).round(4)
overall.columns = ["用户数", "转化数", "转化率"]
print("整体结果:")
display(overall)

by_segment = simpson.groupby(["segment", "group"])["converted"].agg(["count", "sum", "mean"]).round(4)
by_segment.columns = ["用户数", "转化数", "转化率"]
print("分新老用户:")
display(by_segment)

print("各段实验组减对照组的转化率差:")
for segment in ["new", "returning"]:
    part = by_segment.loc[segment]
    diff = part.loc["treatment", "转化率"] - part.loc["control", "转化率"]
    print(f"  {segment}: {diff:+.4f}")


fig, ax = plt.subplots(figsize=(8.6, 4.6))
labels = ["整体", "新用户", "老用户"]
control_rates = [
    overall.loc["control", "转化率"],
    by_segment.loc[("new", "control"), "转化率"],
    by_segment.loc[("returning", "control"), "转化率"],
]
treatment_rates = [
    overall.loc["treatment", "转化率"],
    by_segment.loc[("new", "treatment"), "转化率"],
    by_segment.loc[("returning", "treatment"), "转化率"],
]
positions = np.arange(len(labels))
width = 0.36
ax.bar(positions - width / 2, control_rates, width, label="对照组", color="#4C78A8")
ax.bar(positions + width / 2, treatment_rates, width, label="实验组", color="#E45756")
ax.set_xticks(positions)
ax.set_xticklabels(labels)
ax.set_ylabel("转化率")
ax.set_title("整体结论与分层结论相反")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
for i, value in enumerate(control_rates):
    ax.text(i - width / 2, value + 0.004, f"{value:.1%}", ha="center", fontsize=9)
for i, value in enumerate(treatment_rates):
    ax.text(i + width / 2, value + 0.004, f"{value:.1%}", ha="center", fontsize=9)
fig.tight_layout()
fig.savefig(out / "simpson-paradox.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "simpson-paradox.png")))
plt.close(fig)

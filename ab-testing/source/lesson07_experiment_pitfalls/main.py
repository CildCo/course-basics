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
observed_main = users["group"].value_counts().reindex(["control", "treatment"]).to_numpy()
expected_main = np.array([len(users) / 2, len(users) / 2])
chi2_main, p_main = stats.chisquare(observed_main, expected_main)

print("本课程实验分组:", observed_main)
print("SRM 卡方值:", round(float(chi2_main), 4), "p 值:", round(float(p_main), 4))
print()

observed_bad = np.array([5180, 4820])
expected_bad = np.array([5000, 5000])
chi2_bad, p_bad = stats.chisquare(observed_bad, expected_bad)
print("另一个分流异常的样本:", observed_bad)
print("实验组占比:", f"{observed_bad[1] / observed_bad.sum():.2%}")
print("SRM 卡方值:", round(float(chi2_bad), 4), "p 值:", f"{p_bad:.2e}")
print("结论:", "发现样本比例失衡" if p_bad < 0.001 else "未发现明显失衡")


rng = np.random.default_rng(2026)


def one_peeking_experiment(looks=10, batch=50, p=0.15):
    x1 = 0
    x2 = 0
    n1 = 0
    n2 = 0
    p_values = []
    for _ in range(looks):
        x1 += rng.binomial(batch, p)
        x2 += rng.binomial(batch, p)
        n1 += batch
        n2 += batch
        p1 = x1 / n1
        p2 = x2 / n2
        pooled = (x1 + x2) / (n1 + n2)
        se = math.sqrt(pooled * (1 - pooled) * (2 / n1))
        z_score = (p2 - p1) / se
        p_values.append(2 * stats.norm.sf(abs(z_score)))
    return p_values


reps = 2000
any_significant = 0
final_significant = 0
for _ in range(reps):
    p_values = one_peeking_experiment()
    if any(value < 0.05 for value in p_values):
        any_significant += 1
    if p_values[-1] < 0.05:
        final_significant += 1

print("模拟次数:", reps)
print("只看最后一次的假阳性率:", round(final_significant / reps, 3))
print("偷看 10 次、至少一次显著的假阳性率:", round(any_significant / reps, 3))
print("建议：固定样本量或使用序贯检验，不要看到显著就停。")


daily = pd.read_csv(data_path("daily_channel_metrics.csv"))
daily_agg = daily.groupby(["day", "group"], as_index=False)[["users", "conversions"]].sum()
daily_agg = daily_agg.sort_values(["group", "day"])
daily_agg["cum_users"] = daily_agg.groupby("group")["users"].cumsum()
daily_agg["cum_conversions"] = daily_agg.groupby("group")["conversions"].cumsum()
daily_agg["cum_rate"] = daily_agg["cum_conversions"] / daily_agg["cum_users"]

checkpoints = daily_agg[daily_agg["day"].isin([3, 7, 14, 30])]
pivot = checkpoints.pivot(index="day", columns="group", values="cum_rate").round(4)
pivot["差值"] = (pivot["treatment"] - pivot["control"]).round(4)
print("累计转化率（按天）:")
display(pivot)
print("前几天波动更大，随着样本积累才逐渐稳定。")


true_lift = 0.07
for contamination in [0.0, 0.1, 0.2, 0.3]:
    observed_lift = true_lift * (1 - contamination)
    print(
        f"实验组污染比例 {contamination:.0%} -> "
        f"观察到的提升约 {observed_lift:.2%}"
    )

print()
print("按停留时长筛选后再比较转化率:")
rows = []
for threshold in [0, 60, 120, 180]:
    subset = users[users["session_seconds"] >= threshold]
    rates = subset.groupby("group")["converted"].mean()
    rows.append([
        threshold,
        len(subset),
        round(float(rates["control"]), 4),
        round(float(rates["treatment"]), 4),
        round(float(rates["treatment"] - rates["control"]), 4),
    ])

filtered = pd.DataFrame(rows, columns=["停留时长门槛", "剩余用户数", "对照转化率", "实验转化率", "差值"])
display(filtered)


checklist = pd.DataFrame(
    [
        ["SRM", "两组人数是否符合计划比例", "卡方拟合优度检验"],
        ["偷看", "是否固定样本量或使用序贯方法", "记录检验次数和停止规则"],
        ["污染", "实验组是否真的看到新版", "曝光日志、版本标记"],
        ["幸存者偏差", "分析人群是否实验前定义", "全量用户口径、敏感性分析"],
    ],
    columns=["风险", "检查问题", "证据"],
)
display(checklist)

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

print("数据行数:", len(users))
print("字段:", ", ".join(users.columns))
print()
print(users.head(3).to_string(index=False))
print()
print("分组人数:")
print(users["group"].value_counts().to_string())


summary = users.groupby("group").agg(
    users=("user_id", "count"),
    conversions=("converted", "sum"),
    conversion_rate=("converted", "mean"),
    avg_session_seconds=("session_seconds", "mean"),
    retention_rate=("retained_7d", "mean"),
)
summary["conversion_rate"] = summary["conversion_rate"].round(4)
summary["avg_session_seconds"] = summary["avg_session_seconds"].round(1)
summary["retention_rate"] = summary["retention_rate"].round(4)
display(summary)

control = summary.loc["control"]
treatment = summary.loc["treatment"]
absolute_lift = treatment["conversion_rate"] - control["conversion_rate"]
relative_lift = treatment["conversion_rate"] / control["conversion_rate"] - 1

print("转化率绝对提升:", round(absolute_lift, 4))
print("转化率相对提升:", f"{relative_lift:.1%}")


compare = users.groupby("group")["session_seconds"].agg(
    ["mean", "median", "std", "count"]
).round(1)
display(compare)

print("用户 ID 是否唯一:", users["user_id"].is_unique)
print("缺失值总数:", int(users.isna().sum().sum()))
print("实验组占比:", f"{(users['group'] == 'treatment').mean():.1%}")


metric_roles = pd.DataFrame(
    [
        ["conversion_rate", "主指标", "新版是否让更多人完成注册"],
        ["retention_rate", "护栏指标", "不能为了转化牺牲长期回访"],
        ["avg_session_seconds", "辅助指标", "解释转化变化，不单独下结论"],
    ],
    columns=["指标", "角色", "用途"],
)
display(metric_roles)

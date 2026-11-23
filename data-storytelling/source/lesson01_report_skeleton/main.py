from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, display


np.random.seed(42)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = data_path("sales.csv").parent.parent / "output"
out.mkdir(exist_ok=True)

sales = pd.read_csv(data_path("sales.csv"))
sales["month"] = pd.to_datetime(sales["month"], format="%Y-%m")

PRIMARY = "#2F5D8A"
ACCENT = "#D64545"
MUTED = "#B8CCE4"
INK = "#333333"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": INK,
    "xtick.color": "#666666",
    "ytick.color": "#666666",
})

print("数据行数:", len(sales))
print(sales.head(4).to_string(index=False))


total_revenue = sales["revenue"].sum()
monthly = sales.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
region_revenue = sales.groupby("region")["revenue"].sum().sort_values(ascending=False)
category_revenue = sales.groupby("category")["revenue"].sum().sort_values(ascending=False)

peak = monthly.loc[monthly["revenue"].idxmax()]
last = monthly.iloc[-1]
peak_to_last = last["revenue"] / peak["revenue"] - 1

print(f"上半年总销售额：{total_revenue / 10000:.1f} 万元")
print(f"峰值月份：{peak['month'].month} 月，{peak['revenue'] / 10000:.1f} 万元")
print(f"6 月较峰值：{peak_to_last:.1%}")
print(f"第一大地区：{region_revenue.index[0]}，占比 {region_revenue.iloc[0] / total_revenue:.1%}")
print(f"第一大品类：{category_revenue.index[0]}，占比 {category_revenue.iloc[0] / total_revenue:.1%}")


fig = plt.figure(figsize=(12, 5.2))
gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1.5, 1.0], wspace=0.35)

ax_conclusion = fig.add_subplot(gs[0, 0])
ax_conclusion.axis("off")
ax_conclusion.text(0, 1.0, "结论", fontsize=14, fontweight="bold", color=PRIMARY, va="top")
ax_conclusion.text(
    0, 0.78,
    "上半年销售额 168.5 万元，\n4 月见顶后连续两月回落。",
    fontsize=13, color=INK, va="top", linespacing=1.8,
)
ax_conclusion.text(0, 0.36, "一句话判断：增长动能正在减弱，\n但总量仍高于年初。",
                   fontsize=10, color="#666666", va="top", linespacing=1.7)

ax_evidence = fig.add_subplot(gs[0, 1])
bars = ax_evidence.barh(region_revenue.index[::-1], region_revenue.values[::-1] / 10000,
                        color=MUTED, height=0.58)
bars[-1].set_color(PRIMARY)
ax_evidence.set_title("证据：各地区销售额（万元）", loc="left", fontsize=12)
ax_evidence.set_xlabel("万元")
ax_evidence.spines[["top", "right"]].set_visible(False)
ax_evidence.grid(axis="x", color="#EEEEEE")
ax_evidence.set_axisbelow(True)

ax_action = fig.add_subplot(gs[0, 2])
ax_action.axis("off")
ax_action.text(0, 1.0, "行动", fontsize=14, fontweight="bold", color=ACCENT, va="top")
actions = [
    "1. 复盘华东 5-6 月下滑原因",
    "2. 复制华南、西南的增长动作",
    "3. 把数码作为下半年主推品类",
]
for i, item in enumerate(actions):
    ax_action.text(0, 0.78 - i * 0.18, item, fontsize=11, color=INK, va="top")

fig.suptitle("一页报告的骨架：结论、证据、行动", x=0.02, ha="left", fontsize=17, fontweight="bold")
fig.text(0.02, 0.02, "数据来源：assets/sales.csv（2026 年 1-6 月）", fontsize=9, color="#888888")
fig.savefig(out / "lesson01-skeleton.png", dpi=130, bbox_inches="tight")
display(Image(filename=str(out / "lesson01-skeleton.png")))
plt.close(fig)
print("骨架图已保存：", (out / "lesson01-skeleton.png").name)


def build_skeleton(conclusion, evidence, actions):
    lines = ["【结论】", conclusion, "", "【证据】"]
    lines += [f"- {item}" for item in evidence]
    lines += ["", "【行动】"]
    lines += [f"- {item}" for item in actions]
    return "\n".join(lines)

text = build_skeleton(
    conclusion="上半年销售额 168.5 万元，4 月见顶后连续两月回落。",
    evidence=[
        "4 月销售额 29.6 万元，为半年最高。",
        "6 月销售额 28.4 万元，较 4 月下降 3.9%。",
        "华东贡献 39.4% 的销售额，是最大地区。",
    ],
    actions=[
        "运营复盘华东 5-6 月下滑原因，7 月 10 日前给出清单。",
        "华南、西南延续现有增长动作，优先补充数码库存。",
        "市场部把数码作为下半年主推品类。",
    ],
)
(out / "lesson01-skeleton.txt").write_text(text + "\n", encoding="utf-8")
print(text)
print("\n已写入：", (out / "lesson01-skeleton.txt").name)

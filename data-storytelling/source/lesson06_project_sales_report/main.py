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

monthly = sales.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
region_revenue = sales.groupby("region")["revenue"].sum().sort_values(ascending=False)
category_revenue = sales.groupby("category")["revenue"].sum().sort_values(ascending=False)
region_month = sales.pivot_table(index="month", columns="region", values="revenue", aggfunc="sum")

total = sales["revenue"].sum()
total_orders = int(sales["orders"].sum())
peak = monthly.loc[monthly["revenue"].idxmax()]
last = monthly.iloc[-1]
peak_to_last = last["revenue"] / peak["revenue"] - 1

east = sales[sales["region"] == "华东"]
east_mar_apr = east[east["month"].isin(pd.to_datetime(["2026-03", "2026-04"]))]["revenue"].sum()
east_may_jun = east[east["month"].isin(pd.to_datetime(["2026-05", "2026-06"]))]["revenue"].sum()
east_change = east_may_jun / east_mar_apr - 1

digital = sales[sales["category"] == "数码"]
digital_jan = digital[digital["month"] == pd.Timestamp("2026-01-01")]["revenue"].sum()
digital_jun = digital[digital["month"] == pd.Timestamp("2026-06-01")]["revenue"].sum()
digital_growth = digital_jun / digital_jan - 1
digital_share = digital["revenue"].sum() / total

southwest = sales[sales["region"] == "西南"]
sw_jan = southwest[southwest["month"] == pd.Timestamp("2026-01-01")]["revenue"].sum()
sw_jun = southwest[southwest["month"] == pd.Timestamp("2026-06-01")]["revenue"].sum()
sw_growth = sw_jun / sw_jan - 1

print(f"总销售额：{total / 10000:.1f} 万元，订单数 {total_orders} 单")
print(f"峰值：{peak['month'].month} 月 {peak['revenue'] / 10000:.1f} 万元")
print(f"6 月较 4 月：{peak_to_last:.1%}")
print(f"华东 5-6 月较 3-4 月：{east_change:.1%}")
print(f"数码占比：{digital_share:.1%}，6 月较 1 月：{digital_growth:.1%}")
print(f"西南 6 月较 1 月：{sw_growth:.1%}")


fig = plt.figure(figsize=(12.5, 9.2))
gs = fig.add_gridspec(4, 3, height_ratios=[0.62, 0.55, 1.7, 1.0],
                      hspace=0.5, wspace=0.3)

header = fig.add_subplot(gs[0, :])
header.axis("off")
header.text(0, 0.95, "2026 年上半年销售分析报告", fontsize=23, fontweight="bold",
            color=INK, va="top")
header.text(0, 0.36,
            f"总销售额 {total / 10000:.1f} 万元，4 月见顶后回落；数码与西南是增长抓手",
            fontsize=11.5, color="#666666", va="top")

kpis = [
    ("总销售额", f"{total / 10000:.1f} 万元"),
    ("数码占比", f"{digital_share:.1%}"),
    ("西南 1-6 月增长", f"{sw_growth:.1%}"),
]
for i, (label, value) in enumerate(kpis):
    ax = fig.add_subplot(gs[1, i])
    ax.axis("off")
    ax.text(0, 0.88, label, fontsize=10, color="#777777", va="top")
    ax.text(0, 0.44, value, fontsize=18, fontweight="bold", color=PRIMARY, va="top")

ax_trend = fig.add_subplot(gs[2, :2])
ax_trend.plot(monthly["month"], monthly["revenue"] / 10000,
              color=PRIMARY, linewidth=2.4, marker="o", markersize=5)
ax_trend.scatter([peak["month"]], [peak["revenue"] / 10000], s=95, color=ACCENT, zorder=3)
ax_trend.annotate(f"4 月见顶\n6 月较 4 月 {peak_to_last:.1%}",
                  xy=(peak["month"], peak["revenue"] / 10000),
                  xytext=(monthly["month"].iloc[1], peak["revenue"] / 10000 + 1.2),
                  fontsize=10, color=ACCENT,
                  arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.1))
ax_trend.set_title("月度销售额（万元）", loc="left", fontsize=12)
ax_trend.spines[["top", "right"]].set_visible(False)
ax_trend.grid(axis="y", color="#EEEEEE")
ax_trend.set_axisbelow(True)

ax_region = fig.add_subplot(gs[2, 2])
ordered = region_revenue.sort_values()
colors = [MUTED] * len(ordered)
colors[-1] = ACCENT
ax_region.barh(ordered.index, ordered.values / 10000, color=colors, height=0.6)
ax_region.set_title("地区销售额（万元）", loc="left", fontsize=12)
ax_region.set_xlabel("万元")
ax_region.spines[["top", "right"]].set_visible(False)
ax_region.grid(axis="x", color="#EEEEEE")
ax_region.set_axisbelow(True)
ax_region.text(ordered.iloc[-1] / 10000 - 1.5, len(ordered) - 1,
               f"5-6 月较 3-4 月 {east_change:.1%}", ha="right", va="center",
               fontsize=9, color="white")

ax_note = fig.add_subplot(gs[3, :2])
ax_note.axis("off")
ax_note.text(0, 1.0, "结论与行动", fontsize=12, fontweight="bold", color=ACCENT, va="top")
ax_note.text(0, 0.72,
             "整体在 4 月见顶，5-6 月走弱主要来自华东；\n"
             "数码占比接近六成，西南增长最快。",
             fontsize=11, color=INK, va="top", linespacing=1.7)
ax_note.text(0, 0.16,
             "行动：复盘华东下滑原因 / 复制华南西南动作 / 数码优先备货",
             fontsize=9.5, color="#666666", va="top")

ax_category = fig.add_subplot(gs[3, 2])
ax_category.bar(category_revenue.index, category_revenue.values / total * 100,
                color=[PRIMARY, MUTED], width=0.55)
for i, value in enumerate(category_revenue.values / total * 100):
    ax_category.text(i, value + 1.5, f"{value:.1f}%", ha="center", fontsize=9.5, color=INK)
ax_category.set_ylim(0, 72)
ax_category.set_title("品类占比", loc="left", fontsize=12)
ax_category.set_ylabel("%")
ax_category.spines[["top", "right"]].set_visible(False)
ax_category.grid(axis="y", color="#EEEEEE")
ax_category.set_axisbelow(True)

fig.text(0.01, 0.01, "数据来源：assets/sales.csv（2026 年 1-6 月，48 条记录）；销售额未扣退款",
         fontsize=9, color="#888888")
fig.savefig(out / "sales-report.png", dpi=150, bbox_inches="tight")
display(Image(filename=str(out / "sales-report.png")))
plt.close(fig)
print("一页报告图已保存：", (out / "sales-report.png").name)


region_table = sales.groupby("region").agg(
    销售额=("revenue", "sum"), 订单数=("orders", "sum")
).sort_values("销售额", ascending=False)
table_rows = ["| 地区 | 销售额（万元） | 订单数 |", "| --- | ---: | ---: |"]
for region, row in region_table.iterrows():
    table_rows.append(f"| {region} | {row['销售额'] / 10000:.1f} | {int(row['订单数'])} |")
appendix_table = "\n".join(table_rows)

report = f"""# 2026 年上半年销售分析报告

## 结论

上半年销售额 {total / 10000:.1f} 万元，4 月见顶后 5-6 月连续回落；整体走弱主要来自华东。
数码品类占比 {digital_share:.1%}，6 月较 1 月增长 {digital_growth:.1%}；西南地区 6 月较 1 月增长 {sw_growth:.1%}，是增速最快的地区。

## 关键数字

- 总销售额：{total / 10000:.1f} 万元
- 总订单数：{total_orders} 单
- 峰值月份：{peak['month'].month} 月，{peak['revenue'] / 10000:.1f} 万元
- 6 月较 4 月：{peak_to_last:.1%}
- 华东 5-6 月较 3-4 月：{east_change:.1%}
- 数码销售额占比：{digital_share:.1%}

## 证据

1. **月度趋势**：销售额从 1 月的 26.3 万元升至 4 月的 {peak['revenue'] / 10000:.1f} 万元，随后连续两个月回落，6 月为 {last['revenue'] / 10000:.1f} 万元。
2. **地区结构**：华东贡献 {region_revenue['华东'] / total:.1%} 的销售额，但 5-6 月合计较 3-4 月下降 {abs(east_change):.1%}；华南、西南同期保持增长。
3. **品类结构**：数码贡献 {digital_share:.1%} 的销售额，6 月较 1 月增长 {digital_growth:.1%}；家居占比 {1 - digital_share:.1%}。

## 行动建议

1. 运营团队在 7 月 10 日前复盘华东 5-6 月下滑原因，重点核对促销节奏、库存和渠道变化。
2. 把华南、西南的增长动作整理成可复制清单，优先补充数码品类库存。
3. 下半年以数码为主推品类，家居侧重点转向结构优化，而不是继续平均投放。

## 范围与边界

- 时间范围：2026 年 1-6 月。
- 覆盖范围：华东、华南、华北、西南四个地区，数码与家居两个品类，共 {len(sales)} 条月度汇总记录。
- 口径：销售额为订单金额合计，未扣退款；订单数为月度汇总值。
- 边界：没有上年同期数据，无法计算同比；没有促销、库存、渠道和退款明细，不能判断华东下滑的具体原因。地区与品类之间的同步变化不等于因果关系。

## 附录

{appendix_table}

"""

(out / "sales-report.md").write_text(report, encoding="utf-8")
print(report)
print("\n已写入：", (out / "sales-report.md").name)


for name in ["sales-report.png", "sales-report.md"]:
    path = out / name
    print(f"{name}: {path.stat().st_size:,} 字节")

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

monthly = pd.read_csv(data_path("monthly.csv"))
monthly["month"] = pd.to_datetime(monthly["month"])
print("月度汇总:", monthly.shape[0], "行")
print(monthly.head(3).to_string(index=False))


total_revenue = monthly["revenue"].sum()
last_year_revenue = monthly["revenue_last_year"].sum()
yoy = total_revenue / last_year_revenue - 1
region = monthly.groupby("region")["revenue"].sum().sort_values(ascending=False)
category = monthly.groupby("category")["revenue"].sum().sort_values(ascending=False)

print(f"全年销售额：{total_revenue / 10000:,.1f} 万元")
print(f"同比增长：{yoy:.1%}")
print(f"第一地区：{region.index[0]}，占比 {region.iloc[0] / total_revenue:.1%}")
print(f"第一分类：{category.index[0]}，占比 {category.iloc[0] / total_revenue:.1%}")


from IPython.display import Image, display
import matplotlib.pyplot as plt

total = monthly.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
total["rolling3"] = total["revenue"].rolling(3).mean()
primary = "#2F5D8A"
accent = "#D64545"
muted = "#B8CCE4"

fig = plt.figure(figsize=(12, 8.5))
gs = fig.add_gridspec(3, 3, height_ratios=[0.55, 1.5, 1.0], hspace=0.55, wspace=0.35)

header = fig.add_subplot(gs[0, :])
header.axis("off")
header.text(0.0, 0.95, "2026 年销售一页报告", fontsize=22, fontweight="bold", va="top")
header.text(
    0.0, 0.52,
    f"全年销售额 {total_revenue / 10000:.1f} 万元，同比增长 {yoy:.1%}，{region.index[0]}贡献最高",
    fontsize=12, color="#555555", va="top",
)
header.text(0.0, 0.08, "数据来源：课程示例 monthly.csv", fontsize=9, color="#888888", va="top")

ax_trend = fig.add_subplot(gs[1, :2])
ax_trend.plot(total["month"], total["revenue"], marker="o", color=muted, label="实际销售额")
ax_trend.plot(total["month"], total["rolling3"], color=primary, linewidth=2.5, label="3 个月滚动平均")
ax_trend.set_title("月度趋势：6 月和 12 月是全年高点", loc="left", fontsize=12)
ax_trend.set_ylabel("销售额（元）")
ax_trend.legend(frameon=False, fontsize=9, loc="upper left")
ax_trend.spines[["top", "right"]].set_visible(False)

ax_region = fig.add_subplot(gs[1, 2])
ax_region.barh(region.index[::-1], region.values[::-1] / 10000, color=muted)
ax_region.barh(region.index[0], region.values[0] / 10000, color=accent)
ax_region.set_title("地区：华东领先", loc="left", fontsize=12)
ax_region.set_xlabel("万元")
ax_region.spines[["top", "right"]].set_visible(False)

ax_category = fig.add_subplot(gs[2, :2])
bars = ax_category.bar(category.index, category.values / 10000, color=[primary, "#6F9FC4", muted])
for bar, value in zip(bars, category.values / 10000):
    ax_category.text(
        bar.get_x() + bar.get_width() / 2,
        value + 1,
        f"{value:.1f}",
        ha="center",
        fontsize=9,
    )
ax_category.set_title("分类：数码是最大品类", loc="left", fontsize=12)
ax_category.set_ylabel("销售额（万元）")
ax_category.set_ylim(0, category.max() / 10000 * 1.18)
ax_category.spines[["top", "right"]].set_visible(False)

ax_note = fig.add_subplot(gs[2, 2])
ax_note.axis("off")
ax_note.text(0, 1.0, "结论与动作", fontsize=13, fontweight="bold", va="top")
ax_note.text(
    0, 0.84,
    "1. 守住华东基本盘\n2. 复刻 6 月和 12 月大促节奏\n3. 关注华中数码的异常增长",
    fontsize=10.5, color="#333333", va="top", linespacing=1.8,
)

fig.savefig(out / "report.png", dpi=150, bbox_inches="tight")
display(Image(filename=str(out / "report.png")))
plt.close(fig)
print("已导出:", (out / "report.png").name)


summary_lines = [
    "2026 年销售一页报告",
    f"全年销售额：{total_revenue / 10000:,.1f} 万元",
    f"同比增长：{yoy:.1%}",
    f"第一地区：{region.index[0]}（{region.iloc[0] / total_revenue:.1%}）",
    f"第一分类：{category.index[0]}（{category.iloc[0] / total_revenue:.1%}）",
    "建议：守住华东，复刻大促节奏，跟进华中数码增长。",
]
(out / "report-summary.txt").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
print("\n".join(summary_lines))
print("\n已写入:", (out / "report-summary.txt").name)

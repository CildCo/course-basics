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


from IPython.display import Image, display
import matplotlib.pyplot as plt

total = monthly.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
total["rolling3"] = total["revenue"].rolling(3).mean()

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(total["month"], total["revenue"], marker="o", label="实际销售额", color="#A7C4E4")
ax.plot(total["month"], total["rolling3"], linewidth=2.5, label="3 个月滚动平均", color="#D64545")
peak = total.loc[total["revenue"].idxmax()]
ax.annotate(
    f"峰值 {peak['revenue'] / 10000:.1f} 万",
    xy=(peak["month"], peak["revenue"]),
    xytext=(-60, 18),
    textcoords="offset points",
    arrowprops={"arrowstyle": "->", "color": "#555555"},
)
ax.set_xlabel("月份")
ax.set_ylabel("销售额（元）")
ax.set_title("月度销售额与 3 个月滚动平均")
ax.legend(frameon=False, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(out / "trend-rolling.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "trend-rolling.png")))
plt.close(fig)
print("峰值月份:", peak["month"].strftime("%Y-%m"), "销售额:", f"{peak['revenue']:,.0f}", "元")


last_year = monthly.groupby("month", as_index=False)["revenue_last_year"].sum()
total["mom"] = total["revenue"].pct_change()
total["yoy"] = total["revenue"].to_numpy() / last_year["revenue_last_year"].to_numpy() - 1

view = total.tail(4).copy()
view["mom"] = (view["mom"] * 100).round(1).astype(str) + "%"
view["yoy"] = (view["yoy"] * 100).round(1).astype(str) + "%"
print(view[["month", "revenue", "mom", "yoy"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 4))
values = total["mom"].fillna(0) * 100
colors = ["#D64545" if value < 0 else "#4C78A8" for value in values]
bars = ax.bar(total["month"], values, color=colors, width=20)
for bar, value in zip(bars, values):
    if abs(value) >= 1:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + (0.6 if value >= 0 else -1.6),
            f"{value:.1f}%",
            ha="center",
            fontsize=8,
        )
ax.axhline(0, color="#555555", linewidth=0.8)
ax.set_ylabel("环比（%）")
ax.set_title("月度环比：负增长用另一种颜色")
ax.spines[["top", "right"]].set_visible(False)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(out / "mom.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "mom.png")))
plt.close(fig)
print("12 月环比:", f"{total['mom'].iloc[-1]:.1%}", "同比:", f"{total['yoy'].iloc[-1]:.1%}")


region_month = monthly.pivot_table(index="month", columns="region", values="revenue", aggfunc="sum")
indexed = region_month / region_month.iloc[0] * 100

fig, ax = plt.subplots(figsize=(9, 4.6))
colors = {"华东": "#4C78A8", "华南": "#E45756", "华北": "#54A24B", "华中": "#B279A2"}
for region_name in indexed.columns:
    ax.plot(indexed.index, indexed[region_name], linewidth=2, color=colors[region_name])
    ax.text(
        indexed.index[-1],
        indexed[region_name].iloc[-1],
        region_name,
        fontsize=9,
        color=colors[region_name],
        va="center",
    )
ax.axhline(100, color="#999999", linewidth=0.8, linestyle="--")
ax.set_xlabel("月份")
ax.set_ylabel("指数（1 月 = 100）")
ax.set_title("把各地区起点统一为 100 后比较增速")
ax.spines[["top", "right"]].set_visible(False)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(out / "indexed-region.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "indexed-region.png")))
plt.close(fig)
print(indexed.iloc[-1].round(1).to_string())


region_yoy = monthly.groupby("region")[["revenue", "revenue_last_year"]].sum()
region_yoy["yoy"] = region_yoy["revenue"] / region_yoy["revenue_last_year"] - 1
region_yoy = region_yoy.sort_values("yoy", ascending=False)
for region_name, value in (region_yoy["yoy"] * 100).round(1).items():
    print(f"{region_name}: {value}%")
print("全年同比最高的地区:", region_yoy.index[0])

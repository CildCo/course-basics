from pathlib import Path

from IPython.display import Image, display

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

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

daily = (pd.read_csv(data_path("daily_sales.csv"), parse_dates=["date"])
    .sort_values("date")
    .set_index("date"))
print(daily.head(3).to_string())
print("日期范围:", daily.index.min().date(), "→", daily.index.max().date())
print("天数:", len(daily))


weekly = daily.resample("W")["revenue"].agg(["sum", "mean", "count"]).round(1)
print(weekly.to_string())


daily["rolling_7"] = daily["revenue"].rolling(window=7, min_periods=3).mean().round(1)
print(daily.head(8).to_string())
print("7 日滚动均值最高:", round(float(daily["rolling_7"].max()), 1))


fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(daily.index, daily["revenue"], color="#9AA5B1", linewidth=1.2, label="日销售额")
ax.plot(daily.index, daily["rolling_7"], color="#2F6F8F", linewidth=2.2, label="7 日滚动均值")
ax.set_title("日销售额与 7 日滚动均值")
ax.set_ylabel("销售额（元）")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(out / "resample-rolling.png", dpi=120)
display(Image(filename=str(out / "resample-rolling.png")))
plt.close(fig)

weekend = daily[daily.index.dayofweek >= 5]["revenue"].mean()
weekday = daily[daily.index.dayofweek < 5]["revenue"].mean()
print("周末日均:", round(float(weekend), 1), "工作日日均:", round(float(weekday), 1))


monthly = (pd.read_csv(data_path("monthly_sales.csv"), parse_dates=["month"])
    .set_index("month")
    .sort_index())
monthly["mom"] = monthly["revenue"].pct_change(fill_method=None).round(3)
monthly["yoy"] = (monthly["revenue"] / monthly["revenue"].shift(12) - 1).round(3)
print(monthly.loc["2025"].to_string())


fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(monthly.index, monthly["revenue"], color="#2F6F8F", marker="o", markersize=3)
axes[0].set_title("月度销售额")
axes[0].set_ylabel("销售额（元）")

year_2025 = monthly.loc["2025"]
axes[1].bar(year_2025.index.strftime("%m月"), year_2025["yoy"] * 100, color="#2F6F8F")
axes[1].axhline(0, color="#9AA5B1", linewidth=1)
axes[1].set_title("2025 年各月同比")
axes[1].set_ylabel("同比增幅（%）")

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "monthly-yoy.png", dpi=120)
display(Image(filename=str(out / "monthly-yoy.png")))
plt.close(fig)
print("2025 年平均同比:", round(float(year_2025["yoy"].mean()) * 100, 1), "%")


monthly_from_daily = daily["revenue"].resample("ME").agg(["sum", "mean", "count"]).round(1)
print(monthly_from_daily.to_string())

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import numpy as np
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

orders = pd.read_csv(
    data_path("orders.csv"),
    dtype={"customer_id": "string", "product_id": "string", "order_date": "string"},
)
orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="coerce")
orders["amount"] = pd.to_numeric(orders["amount"], errors="coerce")
print("订单表:", orders.shape)


base = orders.drop_duplicates(subset="order_id", keep="last").copy()
base["order_date"] = pd.to_datetime(base["order_date"], errors="coerce", format="mixed")
expected = (base["quantity"] * base["unit_price"]).round(2)

valid = base[
    base["quantity"].between(1, 99)
    & ((base["amount"] - expected).abs() <= 0.01)
    & base["order_date"].between("2026-01-01", "2026-10-01")
].copy()

print("原始行数:", len(orders))
print("可分析订单:", len(valid))
print("统计期:", valid["order_date"].min().date(), "至", valid["order_date"].max().date())


q1, q3 = valid["amount"].quantile([0.25, 0.75])
iqr = q3 - q1
upper = q3 + 1.5 * iqr
outliers = valid[valid["amount"] > upper]

print(f"Q1={q1:.2f}  Q3={q3:.2f}  IQR={iqr:.2f}  上限={upper:.2f}")
print("金额异常值:", len(outliers), "行")
print(outliers[["order_id", "product_id", "quantity", "amount"]].sort_values("amount", ascending=False).head(6).to_string(index=False))


DIGITAL = ["P006", "P007", "P008", "P009", "P010"]
baseline = valid[valid["order_date"].between("2026-04-01", "2026-06-30")]
current = valid[valid["order_date"].between("2026-07-01", "2026-09-30")]

summary = pd.DataFrame(
    {
        "基线 Q2": [
            len(baseline),
            baseline["amount"].mean(),
            baseline["amount"].quantile(0.95),
            baseline["product_id"].isin(DIGITAL).mean(),
        ],
        "当前 Q3": [
            len(current),
            current["amount"].mean(),
            current["amount"].quantile(0.95),
            current["product_id"].isin(DIGITAL).mean(),
        ],
    },
    index=["订单数", "平均金额", "金额 P95", "数码订单占比"],
)
summary["变化"] = (summary["当前 Q3"] / summary["基线 Q2"] - 1).round(3)
print(summary.round(2).to_string())
print()

mean_drift = current["amount"].mean() / baseline["amount"].mean() - 1
print(f"平均金额漂移: {mean_drift:.1%}；阈值 20% -> {'超限' if abs(mean_drift) > 0.20 else '正常'}")


from IPython.display import Image, display
import matplotlib.pyplot as plt

daily = valid.groupby(valid["order_date"].dt.date).size()
rolling = daily.rolling(7).mean()

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
bins = np.linspace(0, 4000, 25)
axes[0].hist(baseline["amount"], bins=bins, alpha=0.6, label="基线 Q2", color="#4C78A8", density=True)
axes[0].hist(current["amount"], bins=bins, alpha=0.6, label="当前 Q3", color="#E08A3C", density=True)
axes[0].axvline(baseline["amount"].mean(), color="#4C78A8", linestyle="--", linewidth=1)
axes[0].axvline(current["amount"].mean(), color="#E08A3C", linestyle="--", linewidth=1)
axes[0].set_title("订单金额分布：基线 vs 当前")
axes[0].set_xlabel("订单金额（元）")
axes[0].set_ylabel("密度")
axes[0].legend(frameon=False)

axes[1].plot(pd.to_datetime(daily.index), daily.values, color="#BFBFBF", linewidth=0.8, label="每日订单")
axes[1].plot(pd.to_datetime(daily.index), rolling.values, color="#4C78A8", linewidth=2, label="7 日均值")
axes[1].axvline(pd.Timestamp("2026-07-01"), color="#C44E52", linestyle="--", linewidth=1)
axes[1].set_title("每日订单量")
axes[1].set_ylabel("订单数")
axes[1].legend(frameon=False)

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "drift-amount.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "drift-amount.png")))
plt.close(fig)

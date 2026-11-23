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


def check_not_null(frame, columns, threshold=0.0):
    rows = []
    for column in columns:
        missing = int(frame[column].isna().sum())
        rate = missing / len(frame)
        rows.append(
            {
                "column": column,
                "missing": missing,
                "rate": round(rate, 4),
                "passed": rate <= threshold,
            }
        )
    return pd.DataFrame(rows)


key_columns = ["order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price", "amount", "status"]
missing_report = check_not_null(orders, key_columns, threshold=0.01)
print(missing_report.to_string(index=False))


strict = check_not_null(orders, ["order_id", "customer_id", "product_id"], threshold=0.0)
print(strict.to_string(index=False))


from IPython.display import Image, display
import matplotlib.pyplot as plt

rates = missing_report.sort_values("rate")
fig, ax = plt.subplots(figsize=(8, 4.2))
bars = ax.barh(rates["column"], rates["rate"] * 100, color="#4C78A8")
for bar, missing in zip(bars, rates["missing"]):
    if missing:
        bar.set_color("#C44E52")
        bar.set_alpha(0.85)
ax.axvline(1.0, color="#7A7A7A", linestyle="--", linewidth=1)
ax.text(1.05, len(rates) - 0.6, "1% 容忍线", color="#7A7A7A", fontsize=9)
ax.set_xlabel("缺失率（%）")
ax.set_title("订单表字段缺失率")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "missing-rate.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "missing-rate.png")))
plt.close(fig)

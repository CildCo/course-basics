import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

from pathlib import Path

import numpy as np
import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


sales = pd.read_csv(data_path("sales.csv"))
sales["amount"] = sales["units"] * sales["price"]
amount = sales["amount"]

print("均值:", round(amount.mean(), 2))
print("样本方差:", round(amount.var(ddof=1), 2))
print("样本标准差:", round(amount.std(ddof=1), 2))
print("变异系数:", round(amount.std(ddof=1) / amount.mean(), 3))
print("极差:", round(amount.max() - amount.min(), 2))


from IPython.display import Image, display
import matplotlib.pyplot as plt

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(amount, bins=8, color="#5b8def", edgecolor="white")
ax.axvline(amount.mean(), color="#d64545", linestyle="--", linewidth=1.5, label="均值")
ax.axvline(amount.median(), color="#2f9e44", linestyle="--", linewidth=1.5, label="中位数")
ax.set_title("订单金额分布")
ax.set_xlabel("金额（元）")
ax.set_ylabel("订单数")
ax.legend()
fig.tight_layout()
fig.savefig(out / "amount-distribution.png", dpi=120)
display(Image(filename=str(out / "amount-distribution.png")))
print("偏度:", round(amount.skew(), 3))


by_category = sales.groupby("category")["amount"].agg(["count", "mean", "std"])
by_category["cv"] = by_category["std"] / by_category["mean"]
by_category.round(3)


n = len(amount)
standard_error = amount.std(ddof=1) / np.sqrt(n)
print("样本量:", n)
print("标准误:", round(standard_error, 2))
print("均值 ± 1 个标准误:", round(amount.mean() - standard_error, 2), "到", round(amount.mean() + standard_error, 2))

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


from scipy.stats import pearsonr

sales = pd.read_csv(data_path("sales.csv"))
sales["amount"] = sales["units"] * sales["price"]

for left, right in [("units", "amount"), ("price", "units"), ("price", "amount")]:
    r, p = pearsonr(sales[left], sales[right])
    print(f"{left} 与 {right}: r={r:.3f}, p={p:.4f}")


sales[["units", "price", "amount"]].corr().round(3)


sales.groupby("category")[["units", "price"]].mean().round(2)


rng = np.random.default_rng(20261025)
days = 180
temperature = rng.normal(25, 6, days)
ice_cream = 80 + 9 * temperature + rng.normal(0, 25, days)
drowning = 15 + 4 * temperature + rng.normal(0, 12, days)

r, p = pearsonr(ice_cream, drowning)
print(f"冰淇淋销量与溺水人数: r={r:.3f}, p={p:.6f}")
print("两者都随气温上升，但冰淇淋不会导致溺水。")

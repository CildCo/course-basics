from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


import pandas as pd

df = pd.read_csv(data_path("sales.csv"))
df = df.assign(amount=df["units"] * df["price"])
df.head()


df.groupby("category")["amount"].sum().sort_values(ascending=False)


summary = df.groupby("category").agg(
    orders=("product", "count"),
    units=("units", "sum"),
    amount=("amount", "sum"),
).reset_index()
summary


summary.sort_values("amount", ascending=False)

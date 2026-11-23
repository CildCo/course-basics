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


pivot = df.pivot_table(
    index="region",
    columns="category",
    values="amount",
    aggfunc="sum",
    fill_value=0,
)
pivot


df.pivot_table(
    index="region",
    columns="category",
    values="units",
    aggfunc="mean",
    fill_value=0,
).round(1)

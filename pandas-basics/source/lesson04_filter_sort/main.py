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
df.head()


df[df["category"] == "办公"].head()


df[(df["units"] >= 10) & (df["price"] < 50)].head()


df.sort_values("units", ascending=False).head()


df.nlargest(3, "units")[["product", "units", "price"]]

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


df = df.assign(amount=df["units"] * df["price"])
df.head()


mapping = {"办公": "Office", "数码": "Digital", "家居": "Home"}
df["category_en"] = df["category"].map(mapping)
df[["category", "category_en"]].head()


df.rename(columns={"amount": "销售额"}).head()

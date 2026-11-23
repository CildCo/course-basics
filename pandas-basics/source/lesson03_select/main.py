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


df["product"].head()


df[["product", "units"]].head()


df.iloc[0:3, 0:3]


df.loc[0:2, ["date", "product", "units"]]

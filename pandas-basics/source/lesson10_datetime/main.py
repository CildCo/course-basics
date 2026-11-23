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
df["date"] = pd.to_datetime(df["date"])
df.head()


print(df.dtypes)
print(df["date"].min())
print(df["date"].max())


df = df.assign(amount=df["units"] * df["price"], month=df["date"].dt.month)
df[["date", "month", "amount"]].head()


monthly = df.groupby("month")["amount"].sum().reset_index()
monthly

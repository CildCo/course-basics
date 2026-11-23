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
df = df.assign(amount=df["units"] * df["price"])
df.head()


category = df.groupby("category").agg(
    orders=("product", "count"),
    units=("units", "sum"),
    amount=("amount", "sum"),
).reset_index().sort_values("amount", ascending=False)
category


monthly = df.assign(month=df["date"].dt.to_period("M")).groupby("month")["amount"].sum().reset_index()
monthly


from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
category.to_csv(output / "category_report.csv", index=False)
monthly.to_csv(output / "monthly_report.csv", index=False)
print("saved:", sorted(path.name for path in output.glob("*.csv")))

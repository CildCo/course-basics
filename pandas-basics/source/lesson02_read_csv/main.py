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


print(df.shape)
print(df.columns.tolist())
print(df.isna().sum())


print(df.dtypes)


from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
target = output / "sales_copy.csv"
df.to_csv(target, index=False)
print("saved:", target.exists())
print("rows:", len(pd.read_csv(target)))

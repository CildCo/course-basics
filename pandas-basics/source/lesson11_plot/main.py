import matplotlib
matplotlib.use("Agg")

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
summary = df.groupby("category")["amount"].sum().sort_values()
summary


import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

summary.plot(kind="bar", title="分类销售额", color="#4f7cff")
plt.xlabel("分类")
plt.ylabel("销售额")
plt.tight_layout()


from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
summary.plot(kind="bar", title="分类销售额", color="#4f7cff")
plt.tight_layout()
plt.savefig(output / "category_sales.png", dpi=120)
print("saved:", (output / "category_sales.png").exists())

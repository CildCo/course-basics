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

import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False


import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(6, 3))
ax.plot([1, 2, 3, 4], [10, 20, 15, 30])
ax.set_title("第一条折线")
ax.set_xlabel("序号")
ax.set_ylabel("数值")


from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
fig.savefig(output / "first.png", dpi=120)
print("saved:", (output / "first.png").exists())

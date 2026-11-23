from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

ratings = pd.read_csv(data_path("ratings.csv"), parse_dates=["timestamp"])
movies = pd.read_csv(data_path("movies.csv"))

print("评分表形状:", ratings.shape)
print("电影表形状:", movies.shape)
print()
print(ratings.head(5).to_string(index=False))
print()
print("评分分布:")
print(ratings["rating"].value_counts().sort_index().to_string())
print()
print("用户数:", ratings["user_id"].nunique())
print("电影数:", ratings["movie_id"].nunique())
cells = ratings["user_id"].nunique() * ratings["movie_id"].nunique()
print("评分矩阵格子数:", cells)
print("填充率:", round(len(ratings) / cells, 3))


matrix = ratings.pivot(index="user_id", columns="movie_id", values="rating")
print("评分矩阵形状:", matrix.shape)
print("缺失格数:", int(matrix.isna().sum().sum()))

fig, ax = plt.subplots(figsize=(12, 4.8))
im = ax.imshow(matrix.values, aspect="auto", cmap="YlGnBu", vmin=1, vmax=5)
ax.set_xticks(range(len(matrix.columns)))
ax.set_xticklabels(matrix.columns, rotation=90, fontsize=8)
ax.set_yticks(range(len(matrix.index)))
ax.set_yticklabels(matrix.index, fontsize=8)
ax.set_xlabel("电影")
ax.set_ylabel("用户")
ax.set_title("评分矩阵：空白格表示没有评分")
fig.colorbar(im, ax=ax, label="评分")
fig.tight_layout()
fig.savefig(out / "rating-matrix.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "rating-matrix.png")))
plt.close(fig)


user_stats = ratings.groupby("user_id").agg(
    评分数=("rating", "size"),
    平均分=("rating", "mean"),
).round(2)
movie_stats = ratings.groupby("movie_id").agg(
    评分数=("rating", "size"),
    平均分=("rating", "mean"),
).round(2)

print("前 5 位用户的评分情况:")
print(user_stats.head(5).to_string())
print()
print("评分次数最多的 5 部电影:")
top = movie_stats.sort_values("评分数", ascending=False).head(5)
top = top.join(movies.set_index("movie_id")[["title", "genres"]])
print(top.to_string())
print()
print("评分次数最少的 5 部电影:")
bottom = movie_stats.sort_values("评分数").head(5)
bottom = bottom.join(movies.set_index("movie_id")[["title", "genres"]])
print(bottom.to_string())

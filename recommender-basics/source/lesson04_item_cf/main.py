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

from sklearn.metrics.pairwise import cosine_similarity

ratings = pd.read_csv(data_path("ratings.csv"), parse_dates=["timestamp"])
movies = pd.read_csv(data_path("movies.csv"))
matrix = ratings.pivot(index="user_id", columns="movie_id", values="rating")
filled = matrix.fillna(0)

item_similarity = pd.DataFrame(
    cosine_similarity(filled.T),
    index=matrix.columns,
    columns=matrix.columns,
)

for movie_id in ["M01", "M09"]:
    sims = item_similarity.loc[movie_id].drop(movie_id).sort_values(ascending=False).head(5)
    table = pd.DataFrame({"相似度": sims.round(3)}).join(
        movies.set_index("movie_id")[["title", "genres"]]
    )
    title = movies.set_index("movie_id").loc[movie_id, "title"]
    print(title, "的相似电影:")
    print(table.to_string())
    print()


def predict_item_cf(user, movie, k=6):
    rated = matrix.loc[user].dropna()
    sims = item_similarity.loc[movie].drop(movie)
    sims = sims[sims.index.isin(rated.index)]
    top = sims[sims > 0].sort_values(ascending=False).head(k)
    if top.empty:
        return float(matrix[movie].mean())
    values = rated[top.index]
    return float((top * values).sum() / top.abs().sum())


def recommend_item_cf(user, k=6, n=10):
    seen = matrix.loc[user].dropna().index
    scores = {
        movie: predict_item_cf(user, movie, k=k)
        for movie in matrix.columns
        if movie not in seen
    }
    return pd.Series(scores).sort_values(ascending=False).head(n)


target = "U01"
recommendations = recommend_item_cf(target, k=6)
table = pd.DataFrame({"预测评分": recommendations.round(2)}).join(
    movies.set_index("movie_id")[["title", "genres"]]
)
print("给", target, "的物品协同过滤推荐:")
print(table.to_string())


top = item_similarity.loc["M01"].drop("M01").sort_values(ascending=False).head(8)
labels = movies.set_index("movie_id").loc[top.index, "title"]

fig, ax = plt.subplots(figsize=(8, 4.5))
positions = np.arange(len(top))[::-1]
ax.barh(positions, top.values, color="#4C78A8")
ax.set_yticks(positions)
ax.set_yticklabels(labels)
ax.set_xlabel("与《星际穿越》的余弦相似度")
ax.set_title("最相似的 8 部电影")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "item-similarity.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "item-similarity.png")))
plt.close(fig)

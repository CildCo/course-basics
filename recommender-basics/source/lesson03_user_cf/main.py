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

similarity = pd.DataFrame(
    cosine_similarity(filled),
    index=matrix.index,
    columns=matrix.index,
)

for user in ["U01", "U06"]:
    neighbors = similarity.loc[user].drop(user).sort_values(ascending=False).head(5)
    print(user, "的相似用户:")
    print(neighbors.round(3).to_string())
    print()


def predict_user_cf(user, movie, k=5):
    sims = similarity.loc[user].drop(user)
    neighbors = sims.sort_values(ascending=False).head(k)
    rated = matrix[movie].dropna()
    neighbors = neighbors[neighbors.index.isin(rated.index)]
    if neighbors.empty:
        return float(matrix[movie].mean())
    return float((neighbors * rated[neighbors.index]).sum() / neighbors.abs().sum())


def recommend_user_cf(user, k=5, n=10):
    seen = matrix.loc[user].dropna().index
    scores = {
        movie: predict_user_cf(user, movie, k=k)
        for movie in matrix.columns
        if movie not in seen
    }
    return pd.Series(scores).sort_values(ascending=False).head(n)


target = "U01"
recommendations = recommend_user_cf(target, k=5)
table = pd.DataFrame({"预测评分": recommendations.round(2)}).join(
    movies.set_index("movie_id")[["title", "genres"]]
)
print("给", target, "的推荐:")
print(table.to_string())
print()
print("已经看过的电影:")
seen_titles = movies.set_index("movie_id").loc[matrix.loc[target].dropna().index, "title"]
print("、".join(seen_titles.tolist()))


fig, ax = plt.subplots(figsize=(7.5, 6.5))
im = ax.imshow(similarity.values, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(len(matrix.index)))
ax.set_xticklabels(matrix.index, rotation=90, fontsize=8)
ax.set_yticks(range(len(matrix.index)))
ax.set_yticklabels(matrix.index, fontsize=8)
ax.set_title("用户之间的余弦相似度")
fig.colorbar(im, ax=ax, label="相似度")
fig.tight_layout()
fig.savefig(out / "user-similarity.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "user-similarity.png")))
plt.close(fig)


for k in [2, 5, 8]:
    recs = recommend_user_cf("U01", k=k, n=5)
    titles = movies.set_index("movie_id").loc[recs.index, "title"].tolist()
    print("k =", k, ":", "、".join(titles))

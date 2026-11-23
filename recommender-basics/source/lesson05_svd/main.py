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

from sklearn.decomposition import TruncatedSVD

ratings = pd.read_csv(data_path("ratings.csv"), parse_dates=["timestamp"])
movies = pd.read_csv(data_path("movies.csv"))
matrix = ratings.pivot(index="user_id", columns="movie_id", values="rating")

user_mean = matrix.mean(axis=1)
centered = matrix.sub(user_mean, axis=0).fillna(0)

svd = TruncatedSVD(n_components=5, random_state=42)
user_vectors = svd.fit_transform(centered)
item_vectors = svd.components_

print("用户向量形状:", user_vectors.shape)
print("物品向量形状:", item_vectors.shape)
print("奇异值:", np.round(svd.singular_values_, 2))
print("解释方差比例:", np.round(svd.explained_variance_ratio_, 3))
print("累计解释方差:", round(svd.explained_variance_ratio_.sum(), 3))


reconstructed = pd.DataFrame(
    user_vectors @ item_vectors + user_mean.values[:, None],
    index=matrix.index,
    columns=matrix.columns,
)

pairs = pd.DataFrame({"真实": matrix.stack(), "重建": reconstructed.stack()})
rmse = np.sqrt(((pairs["真实"] - pairs["重建"]) ** 2).mean())
print("已知评分的重建 RMSE:", round(rmse, 3))
print("真实评分范围:", int(matrix.min().min()), "到", int(matrix.max().max()))
print("重建评分范围:", round(reconstructed.min().min(), 2), "到", round(reconstructed.max().max(), 2))


def recommend_svd(user, n=10):
    scores = reconstructed.loc[user].copy()
    seen = matrix.loc[user].dropna().index
    scores = scores.drop(seen).sort_values(ascending=False).head(n)
    table = pd.DataFrame({"预测评分": scores.round(2)}).join(
        movies.set_index("movie_id")[["title", "genres"]]
    )
    return table


print()
print("给 U01 的 SVD 推荐:")
print(recommend_svd("U01").to_string())


fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
axes[0].imshow(matrix.values, aspect="auto", cmap="YlGnBu", vmin=1, vmax=5)
axes[0].set_title("真实评分（空白为缺失）")
im = axes[1].imshow(reconstructed.values, aspect="auto", cmap="YlGnBu", vmin=1, vmax=5)
axes[1].set_title("5 维隐因子重建评分")

for ax in axes:
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=90, fontsize=7)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=7)
    ax.set_xlabel("电影")

axes[0].set_ylabel("用户")
fig.colorbar(im, ax=axes, shrink=0.8, label="评分")
fig.savefig(out / "svd-reconstruction.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "svd-reconstruction.png")))
plt.close(fig)


for n in [2, 3, 5, 8]:
    model = TruncatedSVD(n_components=n, random_state=42)
    vectors = model.fit_transform(centered)
    rebuilt = pd.DataFrame(
        vectors @ model.components_ + user_mean.values[:, None],
        index=matrix.index,
        columns=matrix.columns,
    )
    pairs = pd.DataFrame({"真实": matrix.stack(), "重建": rebuilt.stack()})
    score = np.sqrt(((pairs["真实"] - pairs["重建"]) ** 2).mean())
    print("n_components =", n, "  RMSE =", round(score, 3))

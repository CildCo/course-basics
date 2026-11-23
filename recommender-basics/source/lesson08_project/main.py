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

holdout = (
    ratings[ratings["rating"] >= 4]
    .groupby("user_id", group_keys=False)
    .sample(n=3, random_state=11)
)
train = ratings.drop(holdout.index)
matrix = train.pivot(index="user_id", columns="movie_id", values="rating")
users = list(matrix.index)
movies_list = list(matrix.columns)

print("训练集:", train.shape)
print("测试集:", holdout.shape)
print("训练矩阵:", matrix.shape)
print("训练矩阵填充率:", round(matrix.notna().mean().mean(), 3))
print("每位用户的测试条数:", holdout.groupby("user_id").size().unique().tolist())


from sklearn.metrics.pairwise import cosine_similarity

user_mean = matrix.mean(axis=1)
centered = matrix.sub(user_mean, axis=0).fillna(0)
similarity = cosine_similarity(centered)


def popularity_scores(user):
    scores = matrix.notna().sum(axis=0).astype(float) + 0.1 * matrix.mean(axis=0)
    scores[matrix.loc[user].notna()] = -1
    return scores.sort_values(ascending=False)


def user_cf_scores(user, k=5):
    index = users.index(user)
    sims = pd.Series(similarity[index], index=users).drop(user)
    neighbors = sims.sort_values(ascending=False).head(k)
    positions = [users.index(item) for item in neighbors.index]
    weights = neighbors.values
    numerator = (centered.iloc[positions].values * weights[:, None]).sum(axis=0)
    denominator = (
        matrix.iloc[positions].notna().values * np.abs(weights)[:, None]
    ).sum(axis=0)
    predicted = user_mean[user] + np.divide(
        numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0
    )
    scores = pd.Series(predicted.astype(float), index=movies_list)
    scores[matrix.loc[user].notna()] = -1
    return scores.sort_values(ascending=False)


from sklearn.decomposition import TruncatedSVD

item_mean = matrix.mean(axis=0)
item_centered = matrix.sub(item_mean, axis=1).fillna(0)
item_similarity = cosine_similarity(item_centered.T)


def item_cf_scores(user, k=8):
    rated = matrix.loc[user].dropna()
    scores = {}
    for index, movie in enumerate(movies_list):
        sims = pd.Series(item_similarity[index], index=movies_list)
        sims = sims[rated.index].drop(movie, errors="ignore")
        top = sims[sims > 0].sort_values(ascending=False).head(k)
        if top.empty:
            scores[movie] = float(item_mean[movie])
        else:
            deviation = rated[top.index] - item_mean[top.index]
            scores[movie] = float(
                item_mean[movie] + (top * deviation).sum() / top.abs().sum()
            )
    result = pd.Series(scores, dtype=float)
    result[matrix.loc[user].notna()] = -1
    return result.sort_values(ascending=False)


svd = TruncatedSVD(n_components=5, random_state=42)
user_vectors = svd.fit_transform(centered)
reconstructed = pd.DataFrame(
    user_vectors @ svd.components_ + user_mean.values[:, None],
    index=users,
    columns=movies_list,
)


def svd_scores(user):
    scores = reconstructed.loc[user].astype(float)
    scores[matrix.loc[user].notna()] = -1
    return scores.sort_values(ascending=False)


def precision_at_k(recommended, relevant, k):
    return len(set(recommended[:k]) & set(relevant)) / k


def recall_at_k(recommended, relevant, k):
    if not relevant:
        return 0.0
    return len(set(recommended[:k]) & set(relevant)) / len(relevant)


def ndcg_at_k(recommended, relevant, k):
    dcg = sum(
        1 / np.log2(position + 2)
        for position, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal = sum(1 / np.log2(position + 2) for position in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 0.0


def evaluate(scorer, k=5):
    records = []
    for user in users:
        recs = scorer(user).head(k).index.tolist()
        relevant = set(holdout.loc[holdout["user_id"] == user, "movie_id"])
        records.append(
            {
                "Precision@5": precision_at_k(recs, relevant, k),
                "Recall@5": recall_at_k(recs, relevant, k),
                "NDCG@5": ndcg_at_k(recs, relevant, k),
            }
        )
    return pd.DataFrame(records).mean()


models = {
    "热门": popularity_scores,
    "用户CF": user_cf_scores,
    "物品CF": item_cf_scores,
    "SVD": svd_scores,
}
result = pd.DataFrame({name: evaluate(scorer) for name, scorer in models.items()}).T
print("离线评估结果（每位用户留出 3 部喜欢的电影）:")
print(result.round(3).to_string())


fig, ax = plt.subplots(figsize=(9, 4.8))
positions = np.arange(len(result))
width = 0.24
colors = ["#4C78A8", "#F58518", "#54A24B"]
for offset, (column, color) in zip([-width, 0, width], zip(result.columns, colors)):
    ax.bar(positions + offset, result[column], width=width, label=column, color=color)
ax.set_xticks(positions)
ax.set_xticklabels(result.index)
ax.set_ylabel("指标值")
ax.set_title("四种推荐方法的离线评估")
ax.set_ylim(0, 1.0)
ax.legend(frameon=False, ncol=3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "model-comparison.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "model-comparison.png")))
plt.close(fig)


rows = []
for user in ["U01", "U06", "U11"]:
    scores = user_cf_scores(user).head(5)
    table = pd.DataFrame({"预测评分": scores.round(2)}).join(
        movies.set_index("movie_id")[["title", "genres"]]
    )
    table.insert(0, "user_id", user)
    rows.append(table)
    print(user, "的推荐:")
    print(table.to_string())
    print()

recommendations = pd.concat(rows).reset_index().rename(columns={"index": "movie_id"})
recommendations.to_csv(out / "recommendations.csv", index=False)
print("推荐清单已写入:", out / "recommendations.csv")
print("文件行数:", len(recommendations))

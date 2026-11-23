import numpy as np


def precision_at_k(recommended, relevant, k):
    top = recommended[:k]
    return len(set(top) & set(relevant)) / k


def recall_at_k(recommended, relevant, k):
    if not relevant:
        return 0.0
    top = recommended[:k]
    return len(set(top) & set(relevant)) / len(relevant)


def ndcg_at_k(recommended, relevant, k):
    dcg = sum(
        1 / np.log2(position + 2)
        for position, item in enumerate(recommended[:k])
        if item in relevant
    )
    ideal = sum(1 / np.log2(position + 2) for position in range(min(len(relevant), k)))
    return dcg / ideal if ideal else 0.0


recommended = ["A", "B", "C", "D", "E"]
relevant = {"B", "D", "F"}
for k in [3, 5]:
    print(
        "K =", k,
        " Precision =", round(precision_at_k(recommended, relevant, k), 3),
        " Recall =", round(recall_at_k(recommended, relevant, k), 3),
        " NDCG =", round(ndcg_at_k(recommended, relevant, k), 3),
    )


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

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

ratings = pd.read_csv(data_path("ratings.csv"), parse_dates=["timestamp"])
movies = pd.read_csv(data_path("movies.csv"))

holdout = (
    ratings[ratings["rating"] >= 4]
    .groupby("user_id", group_keys=False)
    .sample(n=2, random_state=21)
)
train = ratings.drop(holdout.index)
matrix = train.pivot(index="user_id", columns="movie_id", values="rating")
users = list(matrix.index)
movies_list = list(matrix.columns)

user_mean = matrix.mean(axis=1)
centered = matrix.sub(user_mean, axis=0).fillna(0)
similarity = cosine_similarity(centered)


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


popularity = (
    train.groupby("movie_id").size().reindex(movies_list, fill_value=0).astype(float)
)


def popular_scores(user):
    scores = popularity.copy()
    scores[matrix.loc[user].notna()] = -1
    return scores.sort_values(ascending=False)


rows = []
for user, group in holdout.groupby("user_id"):
    relevant = set(group["movie_id"])
    for name, score in [("热门", popular_scores(user)), ("用户CF", user_cf_scores(user))]:
        recs = score.head(5).index.tolist()
        rows.append(
            {
                "方法": name,
                "Precision@5": precision_at_k(recs, relevant, 5),
                "Recall@5": recall_at_k(recs, relevant, 5),
                "NDCG@5": ndcg_at_k(recs, relevant, 5),
            }
        )

result = pd.DataFrame(rows).groupby("方法").mean().round(3)
print("离线评估结果（每位用户留出 2 部喜欢的电影）:")
print(result.to_string())


recs_by_user = {}
for user in users:
    recs_by_user[user] = user_cf_scores(user).head(10).index.tolist()

curve = []
for k in range(1, 11):
    precisions, recalls, ndcgs = [], [], []
    for user, group in holdout.groupby("user_id"):
        relevant = set(group["movie_id"])
        recs = recs_by_user[user]
        precisions.append(precision_at_k(recs, relevant, k))
        recalls.append(recall_at_k(recs, relevant, k))
        ndcgs.append(ndcg_at_k(recs, relevant, k))
    curve.append(
        {
            "K": k,
            "Precision": np.mean(precisions),
            "Recall": np.mean(recalls),
            "NDCG": np.mean(ndcgs),
        }
    )
curve = pd.DataFrame(curve).set_index("K")
print(curve.round(3).to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
for column, color in [("Precision", "#4C78A8"), ("Recall", "#F58518"), ("NDCG", "#54A24B")]:
    ax.plot(curve.index, curve[column], marker="o", label=column, color=color)
ax.set_xlabel("K")
ax.set_ylabel("指标值")
ax.set_title("用户协同过滤：指标随 K 的变化")
ax.set_xticks(range(1, 11))
ax.set_ylim(0, 1.05)
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "metric-curve.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "metric-curve.png")))
plt.close(fig)

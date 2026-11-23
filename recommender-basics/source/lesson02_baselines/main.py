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

movie_stats = ratings.groupby("movie_id").agg(
    评分数=("rating", "size"),
    平均分=("rating", "mean"),
).join(movies.set_index("movie_id")[["title", "genres"]])

popular = movie_stats.sort_values(["评分数", "平均分"], ascending=False).head(5)
print("全局热门:")
print(popular.to_string())

latest = ratings["timestamp"].max()
recent_ratings = ratings[ratings["timestamp"] >= latest - pd.Timedelta(days=30)]
recent = (
    recent_ratings.groupby("movie_id")
    .agg(评分数=("rating", "size"), 平均分=("rating", "mean"))
    .join(movies.set_index("movie_id")[["title", "genres"]])
    .sort_values(["评分数", "平均分"], ascending=False)
    .head(5)
)
print()
print("最近 30 天热门（截止", latest.date(), "）:")
print(recent.to_string())

rng = np.random.default_rng(42)
random_ids = rng.choice(movies["movie_id"], size=5, replace=False)
print()
print("随机推荐:")
print(movies.set_index("movie_id").loc[random_ids, ["title", "genres"]].to_string())


holdout = (
    ratings[ratings["rating"] >= 4]
    .groupby("user_id", group_keys=False)
    .sample(n=1, random_state=42)
)
train = ratings.drop(holdout.index)

movie_counts = (
    train.groupby("movie_id")
    .size()
    .reindex(movies["movie_id"], fill_value=0)
    .sort_values(ascending=False)
)
recent_cutoff = train["timestamp"].max() - pd.Timedelta(days=30)
recent_counts = (
    train[train["timestamp"] >= recent_cutoff]
    .groupby("movie_id")
    .size()
    .reindex(movies["movie_id"], fill_value=0)
    .sort_values(ascending=False)
)
rng = np.random.default_rng(42)


def pick_top(scores, seen, k=5):
    picked = []
    for movie_id in scores.index:
        if movie_id not in seen:
            picked.append(movie_id)
        if len(picked) == k:
            break
    return picked


hits = {"全局热门": 0, "最近热门": 0, "随机": 0}
for user, row in holdout.set_index("user_id").iterrows():
    seen = set(train.loc[train["user_id"] == user, "movie_id"])
    target = row["movie_id"]
    random_scores = pd.Series(
        rng.random(len(movies)), index=movies["movie_id"]
    ).sort_values(ascending=False)
    baselines = {
        "全局热门": movie_counts,
        "最近热门": recent_counts,
        "随机": random_scores,
    }
    for name, scores in baselines.items():
        if target in pick_top(scores, seen):
            hits[name] += 1

result = pd.DataFrame(
    {"命中次数": pd.Series(hits), "命中率": pd.Series(hits) / len(holdout)}
).round(3)
print("留一法命中率（K=5）:")
print(result.to_string())


top_ids = movie_counts.head(10).index
recent_aligned = recent_counts.reindex(top_ids, fill_value=0)
titles = movies.set_index("movie_id").loc[top_ids, "title"]

fig, ax = plt.subplots(figsize=(10, 4.8))
x = np.arange(len(top_ids))
ax.bar(x - 0.2, movie_counts.loc[top_ids].values, width=0.4, label="全部时间", color="#4C78A8")
ax.bar(x + 0.2, recent_aligned.values, width=0.4, label="最近 30 天", color="#F58518")
ax.set_xticks(x)
ax.set_xticklabels(titles, rotation=35, ha="right")
ax.set_ylabel("评分数")
ax.set_title("全部时间热门与最近 30 天热门的差别")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "baseline-popularity.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "baseline-popularity.png")))
plt.close(fig)

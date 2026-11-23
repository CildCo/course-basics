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

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

movies = pd.read_csv(data_path("movies.csv"))
genres = movies["genres"].str.split(";")
tags = movies["tags"].str.split(";")
labels = [g + t for g, t in zip(genres, tags)]

encoder = MultiLabelBinarizer()
features = encoder.fit_transform(labels)
feature_df = pd.DataFrame(features, index=movies["movie_id"], columns=encoder.classes_)

print("内容特征矩阵:", feature_df.shape)
print("特征词:", "、".join(encoder.classes_))
print()
print(feature_df.loc[["M01", "M09", "M17"], ["科幻", "爱情", "动画", "太空", "成长"]].to_string())


liked = ["M01", "M02", "M07"]
profile = feature_df.loc[liked].mean(axis=0).values.reshape(1, -1)
content_similarity = cosine_similarity(profile, features).ravel()
scores = pd.Series(content_similarity, index=movies["movie_id"]).drop(liked)
scores = scores.sort_values(ascending=False)

table = pd.DataFrame({"内容相似度": scores.head(8).round(3)}).join(
    movies.set_index("movie_id")[["title", "genres", "tags"]]
)
liked_titles = movies.set_index("movie_id").loc[liked, "title"]
print("新用户喜欢:", "、".join(liked_titles.tolist()))
print()
print("内容推荐:")
print(table.to_string())


top = scores.head(10)
labels = movies.set_index("movie_id").loc[top.index, "title"]

fig, ax = plt.subplots(figsize=(8, 4.6))
positions = np.arange(len(top))[::-1]
ax.barh(positions, top.values, color="#54A24B")
ax.set_yticks(positions)
ax.set_yticklabels(labels)
ax.set_xlabel("与用户画像的余弦相似度")
ax.set_title("冷启动用户的内容推荐得分")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "content-cold-start.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "content-cold-start.png")))
plt.close(fig)

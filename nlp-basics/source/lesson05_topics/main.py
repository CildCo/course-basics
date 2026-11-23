from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import numpy as np
import pandas as pd


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

import re

import jieba
import logging

jieba.setLogLevel(logging.ERROR)

STOPWORDS = set("""的 了 是 在 我 也 都 就 和 而 及 与 这 那 有 个 很 还 被 把 对 从 到 说 让 给 着 过 吗 呢 吧 啊 呀 哦 嗯 一 二 三 什么 这个 那个 还是 就是 觉得 一下 一点 比较 非常 真的 时候 可以 因为 所以 但是 不过 而且 已经 自己 人家 里面 东西 感觉 有点 一次 两次 三天 今天 昨天 明天 这次 上次 下次 一个 现在 之后 以后 之前""".split())
KEEP = {"不", "没", "别", "无", "未", "差", "慢", "贵", "坏", "好"}


def clean_text(text):
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[A-Za-z0-9]+", " ", text)
    text = re.sub(r"[^\u4e00-\u9fff]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text):
    words = jieba.lcut(clean_text(text))
    return [w for w in words if (len(w) >= 2 or w in KEEP) and w not in STOPWORDS]

from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

reviews = pd.read_csv(data_path("reviews.csv"))
reviews["joined"] = reviews["text"].map(tokenize).map(" ".join)

tfidf = TfidfVectorizer(token_pattern=r"(?u)\S+", min_df=2, max_df=0.6)
X = tfidf.fit_transform(reviews["joined"])

nmf = NMF(n_components=4, random_state=42, init="nndsvda", max_iter=600)
W = nmf.fit_transform(X)
H = nmf.components_

print("文档-词矩阵:", X.shape)
print("文档-主题矩阵:", W.shape)
print("主题-词矩阵:", H.shape)
print("重构误差:", round(nmf.reconstruction_err_, 3))


terms = np.array(tfidf.get_feature_names_out())

for i, component in enumerate(H):
    top = terms[np.argsort(component)[-8:][::-1]]
    print(f"主题 {i + 1}: " + "、".join(top))


dominant = W.argmax(axis=1) + 1
reviews["topic"] = dominant

print("每个主题的评论数:")
print(reviews["topic"].value_counts().sort_index().to_string())
print("\n主题与人工标签的交叉表:")
print(pd.crosstab(reviews["topic"], reviews["label"]).to_string())


import matplotlib.pyplot as plt
from IPython.display import Image, display

fig, axes = plt.subplots(2, 2, figsize=(11, 8))
for i, (ax, component) in enumerate(zip(axes.flat, H)):
    index = np.argsort(component)[-8:]
    ax.barh(terms[index], component[index], color="#4C78A8")
    ax.set_title(f"主题 {i + 1}")
    ax.set_xlabel("词权重")
    ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("NMF 从评论中提取的四个主题", fontsize=14)
fig.tight_layout()
fig.savefig(out / "nmf-topics.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "nmf-topics.png")))
plt.close(fig)


for topic in range(4):
    index = np.argsort(W[:, topic])[-2:][::-1]
    print(f"== 主题 {topic + 1} ==")
    for i in index:
        print("-", reviews.iloc[i]["text"][:80])

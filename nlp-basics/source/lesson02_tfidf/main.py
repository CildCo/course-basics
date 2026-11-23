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

reviews = pd.read_csv(data_path("reviews.csv"))
reviews["tokens"] = reviews["text"].map(tokenize)
reviews["joined"] = reviews["tokens"].map(" ".join)

print("文档数:", len(reviews))
print("平均词数:", round(reviews["tokens"].map(len).mean(), 1))
print(reviews[["text", "joined"]].head(2).to_string(index=False))


from sklearn.feature_extraction.text import CountVectorizer

count_vec = CountVectorizer(token_pattern=r"(?u)\S+")
X_count = count_vec.fit_transform(reviews["joined"])
vocab = count_vec.get_feature_names_out()

print("词表大小:", len(vocab))
print("矩阵形状:", X_count.shape)
print("非零元素占比: {:.2%}".format(X_count.nnz / (X_count.shape[0] * X_count.shape[1])))
print("词表前 12 个词:", list(vocab[:12]))


first = X_count[0]
pairs = sorted(zip(first.indices, first.data), key=lambda item: item[1], reverse=True)

print("第一条评论:", reviews.loc[0, "text"])
print("非零词及次数:")
for index, value in pairs[:10]:
    print(f"  {vocab[index]}: {int(value)}")


from sklearn.feature_extraction.text import TfidfVectorizer

tfidf = TfidfVectorizer(token_pattern=r"(?u)\S+")
X_tfidf = tfidf.fit_transform(reviews["joined"])

norms = np.sqrt(np.asarray(X_tfidf[:3].multiply(X_tfidf[:3]).sum(axis=1))).ravel()
print("TF-IDF 矩阵:", X_tfidf.shape)
print("前 3 行 L2 范数:", np.round(norms, 3))

for word in ["物流", "质量", "客服", "不错", "差"]:
    if word in tfidf.vocabulary_:
        print(f"{word}: idf={tfidf.idf_[tfidf.vocabulary_[word]]:.3f}")


import matplotlib.pyplot as plt
from IPython.display import Image, display

labels = reviews["label"].to_numpy()
mean_pos = np.asarray(X_tfidf[labels == "正面"].mean(axis=0)).ravel()
mean_neg = np.asarray(X_tfidf[labels == "负面"].mean(axis=0)).ravel()
terms = tfidf.get_feature_names_out()

top_pos = np.argsort(mean_pos)[-10:]
top_neg = np.argsort(mean_neg)[-10:]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
axes[0].barh(terms[top_pos], mean_pos[top_pos], color="#54A24B")
axes[0].set_title("正面评论中平均权重更高的词")
axes[1].barh(terms[top_neg], mean_neg[top_neg], color="#E45756")
axes[1].set_title("负面评论中平均权重更高的词")
for ax in axes:
    ax.set_xlabel("平均 TF-IDF")
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "tfidf-terms.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "tfidf-terms.png")))
plt.close(fig)

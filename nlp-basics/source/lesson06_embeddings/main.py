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
from collections import Counter

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

counter = Counter(word for tokens in reviews["tokens"] for word in tokens)
vocab = [word for word, count in counter.most_common() if count >= 4][:250]
index = {word: i for i, word in enumerate(vocab)}

window = 2
matrix = np.zeros((len(vocab), len(vocab)), dtype=np.float32)
for tokens in reviews["tokens"]:
    ids = [index[word] for word in tokens if word in index]
    for position, word_id in enumerate(ids):
        start = max(0, position - window)
        end = min(len(ids), position + window + 1)
        for other in range(start, end):
            if other != position:
                matrix[word_id, ids[other]] += 1

print("词表大小:", len(vocab))
print("共现矩阵:", matrix.shape)
print("非零元素占比: {:.2%}".format((matrix > 0).mean()))


from sklearn.decomposition import TruncatedSVD

total = matrix.sum()
row_sum = matrix.sum(axis=1, keepdims=True)
col_sum = matrix.sum(axis=0, keepdims=True)

with np.errstate(divide="ignore", invalid="ignore"):
    pmi = np.log((matrix * total) / (row_sum * col_sum))
ppmi = np.maximum(pmi, 0)
ppmi[np.isnan(ppmi)] = 0

svd = TruncatedSVD(n_components=50, random_state=42)
vectors = svd.fit_transform(ppmi)
vectors = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-9)

print("词向量矩阵:", vectors.shape)
print("前 50 个奇异值解释的方差比例:", round(svd.explained_variance_ratio_.sum(), 3))


def nearest(word, n=6):
    word_id = index[word]
    similarities = vectors @ vectors[word_id]
    order = np.argsort(similarities)[::-1]
    result = [(vocab[i], similarities[i]) for i in order if i != word_id][:n]
    return "、".join(f"{w}({s:.2f})" for w, s in result)


for word in ["物流", "质量", "客服", "价格", "包装", "售后"]:
    if word in index:
        print(f"{word}: {nearest(word)}")


import matplotlib.pyplot as plt
from IPython.display import Image, display

seed_words = ["物流", "质量", "客服", "价格", "包装", "售后"]
related = []
for word in seed_words:
    word_id = index[word]
    order = np.argsort(vectors @ vectors[word_id])[::-1]
    for candidate in order:
        candidate_word = vocab[candidate]
        if candidate_word != word and candidate_word not in seed_words and candidate_word not in related:
            related.append(candidate_word)
            break

words = seed_words + related
positions = [index[word] for word in words]
similarity = vectors[positions] @ vectors[positions].T

fig, ax = plt.subplots(figsize=(8.2, 6.6))
image = ax.imshow(similarity, cmap="YlGnBu", vmin=0, vmax=1)
ax.set_xticks(range(len(words)), labels=words, rotation=45, ha="right")
ax.set_yticks(range(len(words)), labels=words)
ax.set_title("种子词与最相近词的余弦相似度")
fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
fig.tight_layout()
fig.savefig(out / "word-vectors.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "word-vectors.png")))
plt.close(fig)

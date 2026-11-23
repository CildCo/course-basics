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

reviews = pd.read_csv(data_path("reviews.csv"))

print("评论条数:", len(reviews))
print("标签分布:")
print(reviews["label"].value_counts().to_string())
print("\n三条原始评论:")
for text in reviews["text"].head(3):
    print("-", text)


import re

import jieba

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

for text in reviews["text"].head(3):
    print("原文:", text)
    print("清洗:", clean_text(text))
    print("分词:", tokenize(text))
    print()


reviews["tokens"] = reviews["text"].map(tokenize)
reviews["token_count"] = reviews["tokens"].map(len)

print(reviews["token_count"].describe().round(1).to_string())
print("\n最短的一条:")
print(reviews.loc[reviews["token_count"].idxmin(), "text"])
print("\n最长的一条:")
print(reviews.loc[reviews["token_count"].idxmax(), "text"])


from collections import Counter

import matplotlib.pyplot as plt
from IPython.display import Image, display

counter = Counter(word for tokens in reviews["tokens"] for word in tokens)
top = counter.most_common(20)
words = [item[0] for item in top][::-1]
values = [item[1] for item in top][::-1]

fig, ax = plt.subplots(figsize=(7.5, 5.5))
ax.barh(words, values, color="#4C78A8")
ax.set_xlabel("出现次数")
ax.set_title("分词后出现最多的 20 个词")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "top-words.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "top-words.png")))
plt.close(fig)

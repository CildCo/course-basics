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
reviews["char_len"] = reviews["text"].str.len()

print(reviews["char_len"].describe().round(1).to_string())
print("正面平均长度:", round(reviews.loc[reviews["label"] == "正面", "char_len"].mean(), 1))
print("负面平均长度:", round(reviews.loc[reviews["label"] == "负面", "char_len"].mean(), 1))


from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def make_pipeline(name):
    classifier = LogisticRegression(max_iter=1000, random_state=42)
    if name == "仅文本长度":
        features = ColumnTransformer([("length", StandardScaler(), ["char_len"])])
        return Pipeline([("features", features), ("model", classifier)])
    if name == "词 1-gram + 长度":
        features = ColumnTransformer([
            ("word", TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\S+"), "joined"),
            ("length", StandardScaler(), ["char_len"]),
        ])
        return Pipeline([("features", features), ("model", classifier)])
    if name == "字符 2-3gram":
        vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 3), min_df=2)
        return Pipeline([("vectorizer", vectorizer), ("model", classifier)])
    if name == "词 1-2gram":
        vectorizer = TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\S+", ngram_range=(1, 2))
        return Pipeline([("vectorizer", vectorizer), ("model", classifier)])
    vectorizer = TfidfVectorizer(analyzer="word", token_pattern=r"(?u)\S+")
    return Pipeline([("vectorizer", vectorizer), ("model", classifier)])


experiments = [
    ("词 1-gram", reviews["joined"]),
    ("词 1-2gram", reviews["joined"]),
    ("字符 2-3gram", reviews["text"]),
    ("仅文本长度", reviews[["char_len"]]),
    ("词 1-gram + 长度", reviews[["joined", "char_len"]]),
]

cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
rows = []
for name, data in experiments:
    scores = cross_val_score(make_pipeline(name), data, reviews["label"], cv=cv, n_jobs=1)
    rows.append({
        "特征": name,
        "平均准确率": round(float(scores.mean()), 4),
        "标准差": round(float(scores.std()), 4),
    })

result = pd.DataFrame(rows).sort_values("平均准确率", ascending=False)
print(result.to_string(index=False))


import matplotlib.pyplot as plt
from IPython.display import Image, display

plot_data = result.sort_values("平均准确率")
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.barh(
    plot_data["特征"],
    plot_data["平均准确率"],
    xerr=plot_data["标准差"],
    color="#4C78A8",
    capsize=3,
)
ax.set_xlim(0.4, 1.0)
ax.set_xlabel("4 折交叉验证平均准确率")
ax.set_title("不同文本特征的交叉验证结果")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "feature-compare.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "feature-compare.png")))
plt.close(fig)


char_vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 3))
analyzer = char_vectorizer.build_analyzer()

sentence = "物流太慢，包装也有点简陋"
print("原句:", sentence)
print("字符 2-3gram:", analyzer(sentence)[:12])

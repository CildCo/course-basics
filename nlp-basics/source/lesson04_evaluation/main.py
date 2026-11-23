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

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

reviews = pd.read_csv(data_path("reviews.csv"))
reviews["joined"] = reviews["text"].map(tokenize).map(" ".join)

train_df, test_df = train_test_split(
    reviews, test_size=0.3, random_state=42, stratify=reviews["label"]
)

X_train, y_train = train_df["joined"], train_df["label"]
X_test, y_test = test_df["joined"].reset_index(drop=True), test_df["label"].reset_index(drop=True)

pipe = Pipeline([
    ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\S+")),
    ("model", MultinomialNB()),
]).fit(X_train, y_train)

pred = pipe.predict(X_test)
proba = pipe.predict_proba(X_test)
print("测试集:", len(y_test), "条")
print("准确率:", round(accuracy_score(y_test, pred), 3))


from sklearn.metrics import classification_report, confusion_matrix

cm = confusion_matrix(y_test, pred, labels=["正面", "负面"])
print(cm)
print(classification_report(y_test, pred, digits=3))


import matplotlib.pyplot as plt
from IPython.display import Image, display

fig, ax = plt.subplots(figsize=(5.4, 4.6))
image = ax.imshow(cm, cmap="Blues")
for i in range(2):
    for j in range(2):
        color = "white" if cm[i, j] > cm.max() / 2 else "#1f2933"
        ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontsize=14)

ax.set_xticks([0, 1], labels=["预测正面", "预测负面"])
ax.set_yticks([0, 1], labels=["真实正面", "真实负面"])
ax.set_title("朴素贝叶斯的混淆矩阵")
ax.set_xlabel("预测标签")
ax.set_ylabel("真实标签")
fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
fig.tight_layout()
fig.savefig(out / "confusion-matrix.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "confusion-matrix.png")))
plt.close(fig)


errors = pd.DataFrame({
    "text": test_df["text"].to_numpy(),
    "true": y_test.to_numpy(),
    "pred": pred,
    "confidence": proba.max(axis=1),
})
errors = errors[errors["true"] != errors["pred"]].sort_values("confidence", ascending=False)

print("错分条数:", len(errors))
print(errors.head(8).to_string(index=False))


from sklearn.metrics import recall_score

pos_index = y_train[y_train == "正面"].index[:16]
neg_index = y_train[y_train == "负面"].index
X_small = pd.concat([X_train.loc[pos_index], X_train.loc[neg_index]])
y_small = pd.concat([y_train.loc[pos_index], y_train.loc[neg_index]])

print("不平衡训练集:")
print(y_small.value_counts().to_string())

small_pipe = Pipeline([
    ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\S+")),
    ("model", MultinomialNB()),
]).fit(X_small, y_small)

small_pred = small_pipe.predict(X_test)
small_cm = confusion_matrix(y_test, small_pred, labels=["正面", "负面"])

print("准确率:", round(accuracy_score(y_test, small_pred), 3))
print("正面召回率:", round(recall_score(y_test, small_pred, pos_label="正面"), 3))
print("负面召回率:", round(recall_score(y_test, small_pred, pos_label="负面"), 3))
print("混淆矩阵:")
print(small_cm)


fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3))
titles = ["平衡训练集", "不平衡训练集"]
matrices = [cm, small_cm]

for ax, matrix, title in zip(axes, matrices, titles):
    image = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(cm.max(), small_cm.max()))
    for i in range(2):
        for j in range(2):
            color = "white" if matrix[i, j] > matrix.max() / 2 else "#1f2933"
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color=color, fontsize=13)
    ax.set_xticks([0, 1], labels=["预测正面", "预测负面"])
    ax.set_yticks([0, 1], labels=["真实正面", "真实负面"])
    ax.set_title(title)

fig.suptitle("训练集不平衡让正面召回明显下降", fontsize=14)
fig.tight_layout()
fig.savefig(out / "imbalance.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "imbalance.png")))
plt.close(fig)

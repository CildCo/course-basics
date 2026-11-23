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

from sklearn.model_selection import train_test_split

reviews = pd.read_csv(data_path("reviews.csv"))
reviews["joined"] = reviews["text"].map(tokenize).map(" ".join)

train_df, test_df = train_test_split(
    reviews,
    test_size=0.3,
    random_state=42,
    stratify=reviews["label"],
)

X_train, y_train = train_df["joined"], train_df["label"]
X_test, y_test = test_df["joined"], test_df["label"]

print("训练集:", len(train_df), "条；测试集:", len(test_df), "条")
print("训练集标签分布:")
print(y_train.value_counts().to_string())
print("测试集标签分布:")
print(y_test.value_counts().to_string())


from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC


def make_pipeline(model):
    return Pipeline([
        ("tfidf", TfidfVectorizer(token_pattern=r"(?u)\S+")),
        ("model", model),
    ])


models = {
    "多数类基线": DummyClassifier(strategy="most_frequent"),
    "朴素贝叶斯": MultinomialNB(),
    "线性 SVM": LinearSVC(random_state=42),
}

rows = []
for name, model in models.items():
    pipe = make_pipeline(model)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    rows.append({"模型": name, "测试准确率": round(accuracy_score(y_test, pred), 3)})

print(pd.DataFrame(rows).sort_values("测试准确率", ascending=False).to_string(index=False))


from sklearn.metrics import classification_report

for name in ["朴素贝叶斯", "线性 SVM"]:
    pipe = make_pipeline(models[name]).fit(X_train, y_train)
    pred = pipe.predict(X_test)
    print("==", name, "==")
    print(classification_report(y_test, pred, digits=3))


svm = make_pipeline(LinearSVC(random_state=42)).fit(X_train, y_train)
vectorizer = svm.named_steps["tfidf"]
classifier = svm.named_steps["model"]
coef = classifier.coef_[0]
terms = vectorizer.get_feature_names_out()

print("类别顺序:", list(classifier.classes_))
print("更偏向负面的词:", "、".join(terms[np.argsort(coef)[-10:]][::-1]))
print("更偏向正面的词:", "、".join(terms[np.argsort(coef)[:10]]))

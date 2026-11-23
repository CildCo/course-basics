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
    reviews, test_size=0.3, random_state=42, stratify=reviews["label"]
)

X_train, y_train = train_df["joined"], train_df["label"]
X_test, y_test = test_df["joined"], test_df["label"]

print("训练集:", len(train_df), "条；测试集:", len(test_df), "条")
print("训练集标签:")
print(y_train.value_counts().to_string())
print("测试集标签:")
print(y_test.value_counts().to_string())


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

nb_pipe = Pipeline([
    ("vectorizer", TfidfVectorizer(token_pattern=r"(?u)\S+")),
    ("model", MultinomialNB()),
]).fit(X_train, y_train)
nb_pred = nb_pipe.predict(X_test)

print("朴素贝叶斯 测试准确率:", round(accuracy_score(y_test, nb_pred), 3))

cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
cv_rows = []
for C in [0.1, 0.5, 1.0, 2.0, 5.0]:
    pipe = Pipeline([
        ("vectorizer", TfidfVectorizer(token_pattern=r"(?u)\S+")),
        ("model", LinearSVC(C=C, random_state=42)),
    ])
    scores = cross_val_score(pipe, X_train, y_train, cv=cv, n_jobs=1)
    cv_rows.append((C, float(scores.mean()), float(scores.std())))
    print(f"C={C}: {scores.mean():.3f} ± {scores.std():.3f}")

best_C = max(cv_rows, key=lambda item: item[1])[0]
print("\n选择 C =", best_C)

svm_pipe = Pipeline([
    ("vectorizer", TfidfVectorizer(token_pattern=r"(?u)\S+")),
    ("model", LinearSVC(C=best_C, random_state=42)),
]).fit(X_train, y_train)
svm_pred = svm_pipe.predict(X_test)

print("线性 SVM 测试准确率:", round(accuracy_score(y_test, svm_pred), 3))
print("正面召回率:", round(recall_score(y_test, svm_pred, pos_label="正面"), 3))
print("负面召回率:", round(recall_score(y_test, svm_pred, pos_label="负面"), 3))
print()
print(classification_report(y_test, svm_pred, digits=3))


import matplotlib.pyplot as plt
from IPython.display import Image, display
from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_test, svm_pred, labels=["正面", "负面"])

fig, ax = plt.subplots(figsize=(5.4, 4.6))
image = ax.imshow(cm, cmap="Blues")
for i in range(2):
    for j in range(2):
        color = "white" if cm[i, j] > cm.max() / 2 else "#1f2933"
        ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color, fontsize=14)

ax.set_xticks([0, 1], labels=["预测正面", "预测负面"])
ax.set_yticks([0, 1], labels=["真实正面", "真实负面"])
ax.set_title("线性 SVM 的混淆矩阵")
ax.set_xlabel("预测标签")
ax.set_ylabel("真实标签")
fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
fig.tight_layout()
fig.savefig(out / "project-confusion.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "project-confusion.png")))
plt.close(fig)


decision = svm_pipe.decision_function(X_test)

error_table = pd.DataFrame({
    "text": test_df["text"].to_numpy(),
    "true": y_test.to_numpy(),
    "pred": svm_pred,
    "decision": decision,
})
error_table["margin"] = error_table["decision"].abs()

errors = error_table[error_table["true"] != error_table["pred"]].sort_values(
    "margin", ascending=False
)
errors.to_csv(out / "error-report.csv", index=False, encoding="utf-8-sig")

print("错分条数:", len(errors))
print(errors.head(8)[["text", "true", "pred", "margin"]].to_string(index=False))


vectorizer = svm_pipe.named_steps["vectorizer"]
classifier = svm_pipe.named_steps["model"]
coef = classifier.coef_[0]
terms = vectorizer.get_feature_names_out()

positive_index = np.argsort(coef)[:10]
negative_index = np.argsort(coef)[-10:]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
axes[0].barh(terms[positive_index], -coef[positive_index], color="#54A24B")
axes[0].set_title("更偏向正面的词")
axes[1].barh(terms[negative_index], coef[negative_index], color="#E45756")
axes[1].set_title("更偏向负面的词")
for ax in axes:
    ax.set_xlabel("权重绝对值")
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "keywords.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "keywords.png")))
plt.close(fig)

print("偏向正面的词:", "、".join(terms[positive_index]))
print("偏向负面的词:", "、".join(terms[negative_index][::-1]))


import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, recall_score

accuracy = accuracy_score(y_test, svm_pred)
positive_recall = recall_score(y_test, svm_pred, pos_label="正面")
negative_recall = recall_score(y_test, svm_pred, pos_label="负面")

lines = [
    "# 评论情感分类报告",
    "",
    "## 数据",
    "",
    f"- 评论总数：{len(reviews)} 条",
    f"- 训练集：{len(train_df)} 条；测试集：{len(test_df)} 条",
    "- 标签：正面 / 负面",
    "",
    "## 模型",
    "",
    "- 文本处理：正则清洗 + jieba 分词 + 停用词过滤",
    "- 特征：TF-IDF 词特征",
    f"- 分类器：线性 SVM，C={best_C}（训练集 4 折交叉验证选择）",
    "",
    "## 测试集结果",
    "",
    f"- 准确率：{accuracy:.3f}",
    f"- 正面召回率：{positive_recall:.3f}",
    f"- 负面召回率：{negative_recall:.3f}",
    f"- 错分条数：{len(errors)}",
    "",
    "## 错误分析",
    "",
    "错分样本已写入 error-report.csv。优先检查 margin 较大的样本，",
    "常见原因包括混合情感、反讽、隐含否定和标注不一致。",
    "",
    "## 适用边界",
    "",
    "这批数据是教学用的小样本评论，主题集中、情感词明显。",
    "换到真实业务前，需要补充更多领域数据，并重新检查标签质量。",
]
report_text = "\n".join(lines)
(out / "report.md").write_text(report_text, encoding="utf-8")

print(report_text)

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

SEED = 42
np.random.seed(SEED)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

df = pd.read_csv(data_path("customer_churn.csv"), parse_dates=["signup_date"])
df["support_notes"] = df["support_notes"].fillna("")
notes = df["support_notes"]

print("有备注客户:", int((notes.str.len() > 0).sum()), f"({(notes.str.len() > 0).mean():.1%})")
print("平均字数:", round(float(notes.str.len().mean()), 1))
print("最长备注字数:", int(notes.str.len().max()))
display(df.assign(note_length=notes.str.len()).groupby("churned")["note_length"].agg(["mean", "median", "count"]).round(1))
display(df.loc[notes.str.len() > 0, ["support_notes", "churned"]].head(6))


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

train, test = train_test_split(
    df, test_size=0.25, stratify=df["churned"], random_state=SEED
)

vectorizer = TfidfVectorizer(max_features=400, ngram_range=(1, 2), min_df=3)
X_train = vectorizer.fit_transform(train["support_notes"])
X_test = vectorizer.transform(test["support_notes"])

text_model = LogisticRegression(max_iter=1000, random_state=SEED)
text_model.fit(X_train, train["churned"])
tfidf_auc = roc_auc_score(test["churned"], text_model.predict_proba(X_test)[:, 1])

print("训练矩阵:", X_train.shape, "测试矩阵:", X_test.shape)
print("词表大小:", len(vectorizer.vocabulary_))
print("非零比例:", f"{X_train.nnz / (X_train.shape[0] * X_train.shape[1]):.2%}")
print("TF-IDF 测试 AUC:", round(tfidf_auc, 3))


coefficients = pd.Series(
    text_model.coef_[0], index=vectorizer.get_feature_names_out()
).sort_values()
top_terms = pd.concat([coefficients.head(8), coefficients.tail(8)])

fig, ax = plt.subplots(figsize=(8, 5.5))
colors = ["#4C78A8" if value < 0 else "#C44E52" for value in top_terms.values]
ax.barh(top_terms.index, top_terms.values, color=colors)
ax.axvline(0, color="#333333", linewidth=0.8)
ax.set_xlabel("逻辑回归系数（负：留存 / 正：流失）")
ax.set_title("TF-IDF 特征里权重最大的词")
ax.grid(axis="x", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "text-coefficients.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "text-coefficients.png")))
plt.close(fig)
print("最推向流失的词:", ", ".join(top_terms.tail(3).index))
print("最推向留存的词:", ", ".join(top_terms.head(3).index))


from sklearn.feature_extraction.text import HashingVectorizer

hasher = HashingVectorizer(
    n_features=2 ** 10,
    alternate_sign=False,
    ngram_range=(1, 2),
    norm="l2",
)
H_train = hasher.transform(train["support_notes"])
H_test = hasher.transform(test["support_notes"])

hash_model = LogisticRegression(max_iter=1000, random_state=SEED)
hash_model.fit(H_train, train["churned"])
hash_auc = roc_auc_score(test["churned"], hash_model.predict_proba(H_test)[:, 1])

print("哈希维度:", H_train.shape[1])
print("哈希矩阵非零比例:", f"{H_train.nnz / (H_train.shape[0] * H_train.shape[1]):.2%}")
print("哈希测试 AUC:", round(hash_auc, 3))
print("TF-IDF 测试 AUC:", round(tfidf_auc, 3))
print("哈希与 TF-IDF 的差距:", round(hash_auc - tfidf_auc, 3))

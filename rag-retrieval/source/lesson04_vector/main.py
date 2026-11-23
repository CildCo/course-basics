from pathlib import Path
import math
import re
import time
from collections import Counter

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

def tokenize(text):
    text = str(text).lower()
    tokens = []
    for chunk in re.findall(r"[a-z0-9_./:+-]+|[一-鿿]+", text):
        if re.fullmatch(r"[一-鿿]+", chunk):
            if len(chunk) == 1:
                tokens.append(chunk)
            else:
                tokens.extend(chunk[i:i + 2] for i in range(len(chunk) - 1))
        else:
            chunk = chunk.strip(".,;:!?()[]{}")
            if re.search(r"[a-z0-9]", chunk):
                tokens.append(chunk)
    return tokens

def load_documents(folder):
    docs = []
    for path in sorted(folder.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = path.stem
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        docs.append({"doc_id": path.stem, "title": title, "text": text})
    return docs


def parse_sections(text):
    sections = []
    heading = "正文"
    buffer = []
    for line in text.splitlines():
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if buffer:
                body = "\n".join(buffer).strip()
                if body:
                    sections.append((heading, body))
            heading = line[3:].strip()
            buffer = []
        else:
            buffer.append(line)
    if buffer:
        body = "\n".join(buffer).strip()
        if body:
            sections.append((heading, body))
    return sections

def split_long_text(text, max_chars=320, overlap=60):
    sentences = re.split(r"(?<=[。！？；\n])", text)
    pieces = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            start = 0
            while start < len(sentence):
                pieces.append(sentence[start:start + max_chars])
                start += max_chars - overlap
        elif len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            if current:
                pieces.append(current)
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def split_documents(docs, max_chars=360, overlap=60):
    chunks = []
    for doc in docs:
        index = 0
        for heading, body in parse_sections(doc["text"]):
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
            pieces = []
            buffer = ""
            for paragraph in paragraphs:
                if len(paragraph) > max_chars:
                    if buffer:
                        pieces.append(buffer)
                        buffer = ""
                    pieces.extend(split_long_text(paragraph, max_chars, overlap))
                elif len(buffer) + len(paragraph) + 1 <= max_chars:
                    buffer = (buffer + "\n" + paragraph).strip()
                else:
                    if buffer:
                        pieces.append(buffer)
                    buffer = paragraph
            if buffer:
                pieces.append(buffer)
            for piece in pieces:
                index += 1
                chunks.append(
                    {
                        "chunk_id": f"{doc['doc_id']}#{index:02d}",
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "heading": heading,
                        "text": piece,
                        "chars": len(piece),
                        "search_text": f"{doc['title']} {heading} {piece}",
                    }
                )
    return pd.DataFrame(chunks)

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

docs = load_documents(data_path("docs"))
chunks = split_documents(docs)
corpus = [" ".join(tokenize(t)) for t in chunks["search_text"]]

vectorizer = TfidfVectorizer(token_pattern=r"(?u)\S+", lowercase=False, sublinear_tf=True)
X_tfidf = vectorizer.fit_transform(corpus)

n_components = min(48, X_tfidf.shape[0] - 1, X_tfidf.shape[1] - 1)
svd = TruncatedSVD(n_components=n_components, random_state=42)
X_svd = svd.fit_transform(X_tfidf)
X_svd_norm = X_svd / np.clip(np.linalg.norm(X_svd, axis=1, keepdims=True), 1e-9, None)

print("TF-IDF 矩阵:", X_tfidf.shape)
print("SVD 向量:", X_svd.shape)
print("保留方差合计: {:.2%}".format(svd.explained_variance_ratio_.sum()))
print("前 10 个分量解释率:", np.round(svd.explained_variance_ratio_[:10], 3))


def tfidf_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    return (X_tfidf @ query_vector.T).toarray().ravel()


def vector_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    query_svd = svd.transform(query_vector).ravel()
    query_norm = query_svd / max(float(np.linalg.norm(query_svd)), 1e-9)
    return X_svd_norm @ query_norm


def top_table(scores, k=5):
    order = [index for index in np.argsort(-scores) if scores[index] > 0][:k]
    rows = []
    for rank, index in enumerate(order, 1):
        row = chunks.iloc[index]
        rows.append(
            {
                "排名": rank,
                "chunk_id": row["chunk_id"],
                "文档": row["doc_id"],
                "章节": row["heading"],
                "分数": round(float(scores[index]), 3),
            }
        )
    return pd.DataFrame(rows)


query = "密码想不起来了"
tfidf_rank = top_table(tfidf_scores(query))
vector_rank = top_table(vector_scores(query))
tfidf_rank.insert(0, "方法", "TF-IDF")
vector_rank.insert(0, "方法", "SVD 向量")
print("查询：", query)
display(pd.concat([tfidf_rank, vector_rank], ignore_index=True))


fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

ratio = svd.explained_variance_ratio_
axes[0].plot(np.arange(1, len(ratio) + 1), np.cumsum(ratio), marker="o", ms=3, color="#4C78A8")
axes[0].axhline(0.9, color="#C44E52", linestyle="--", linewidth=1)
axes[0].set_xlabel("SVD 分量数")
axes[0].set_ylabel("累计解释方差")
axes[0].set_title("降维保留了多少信息")

query = "密码想不起来了"
tfidf_all = tfidf_scores(query)
vector_all = vector_scores(query)
union = sorted(
    set(np.argsort(-tfidf_all)[:6]) | set(np.argsort(-vector_all)[:6]),
    key=lambda index: -tfidf_all[index],
)
labels = [chunks.iloc[index]["chunk_id"] for index in union]
y = np.arange(len(union))
axes[1].barh(y - 0.19, [tfidf_all[i] for i in union], 0.36, label="TF-IDF", color="#4C78A8")
axes[1].barh(y + 0.19, [vector_all[i] for i in union], 0.36, label="SVD 余弦", color="#54A24B")
axes[1].set_yticks(y)
axes[1].set_yticklabels(labels, fontsize=8)
axes[1].invert_yaxis()
axes[1].set_xlabel("原始分数")
axes[1].set_title("同一查询的候选分数")
axes[1].legend(fontsize=8)

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "svd-scores.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "svd-scores.png")))
plt.close(fig)

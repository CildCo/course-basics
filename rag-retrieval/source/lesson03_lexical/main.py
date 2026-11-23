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

class BM25:
    def __init__(self, tokenized, k1=1.5, b=0.75):
        self.tokenized = tokenized
        self.doc_len = np.array([len(t) for t in tokenized], dtype=float)
        self.avgdl = self.doc_len.mean()
        self.k1 = k1
        self.b = b
        self.df = Counter()
        for tokens in tokenized:
            self.df.update(set(tokens))
        n = len(tokenized)
        self.idf = {
            term: math.log(1 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in self.df.items()
        }

    def scores(self, query):
        q_tokens = tokenize(query)
        scores = np.zeros(len(self.tokenized))
        for i, tokens in enumerate(self.tokenized):
            tf = Counter(tokens)
            total = 0.0
            for term in q_tokens:
                if term not in tf:
                    continue
                freq = tf[term]
                denom = freq + self.k1 * (
                    1 - self.b + self.b * self.doc_len[i] / self.avgdl
                )
                total += self.idf.get(term, 0.0) * freq * (self.k1 + 1) / denom
            scores[i] = total
        return scores

from sklearn.feature_extraction.text import TfidfVectorizer

docs = load_documents(data_path("docs"))
chunks = split_documents(docs)
corpus = [" ".join(tokenize(t)) for t in chunks["search_text"]]

vectorizer = TfidfVectorizer(token_pattern=r"(?u)\S+", lowercase=False, sublinear_tf=True)
X_tfidf = vectorizer.fit_transform(corpus)
tokenized = [tokenize(t) for t in chunks["search_text"]]
bm25 = BM25(tokenized)

print("片段数:", len(chunks))
print("词项数:", X_tfidf.shape[1])
print("TF-IDF 矩阵:", X_tfidf.shape)
print("非零元素比例: {:.2%}".format(X_tfidf.nnz / (X_tfidf.shape[0] * X_tfidf.shape[1])))
print("示例词项:", [term for term in vectorizer.get_feature_names_out() if re.search(r"[一-鿿]", term)][:15])
print("查询切词:", tokenize("忘记密码怎么重置")[:12])


def tfidf_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    return (X_tfidf @ query_vector.T).toarray().ravel()


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


query = "忘记密码怎么重置"
print("查询：", query)
print("TF-IDF 前 5")
display(top_table(tfidf_scores(query)))
print("BM25 前 5")
display(top_table(bm25.scores(query)))


def minmax(values):
    low, high = float(values.min()), float(values.max())
    if high - low < 1e-9:
        return np.zeros_like(values)
    return (values - low) / (high - low)


query = "忘记密码怎么重置"
tfidf_all = tfidf_scores(query)
bm25_all = bm25.scores(query)
union = sorted(
    set(np.argsort(-tfidf_all)[:6]) | set(np.argsort(-bm25_all)[:6]),
    key=lambda index: -tfidf_all[index],
)
labels = [chunks.iloc[index]["chunk_id"] for index in union]

fig, ax = plt.subplots(figsize=(10, 4.2))
x = np.arange(len(union))
width = 0.38
ax.bar(x - width / 2, minmax(tfidf_all)[union], width, label="TF-IDF", color="#4C78A8")
ax.bar(x + width / 2, minmax(bm25_all)[union], width, label="BM25", color="#F58518")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=35, ha="right")
ax.set_ylabel("归一化分数")
ax.set_title("同一查询下两种词法检索的分数")
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "lexical-scores.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "lexical-scores.png")))
plt.close(fig)

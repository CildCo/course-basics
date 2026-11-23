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

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

docs = load_documents(data_path("docs"))
chunks = split_documents(docs)
corpus = [" ".join(tokenize(t)) for t in chunks["search_text"]]

vectorizer = TfidfVectorizer(token_pattern=r"(?u)\S+", lowercase=False, sublinear_tf=True)
X_tfidf = vectorizer.fit_transform(corpus)
tokenized = [tokenize(t) for t in chunks["search_text"]]
bm25 = BM25(tokenized)

n_components = min(48, X_tfidf.shape[0] - 1, X_tfidf.shape[1] - 1)
svd = TruncatedSVD(n_components=n_components, random_state=42)
X_svd = svd.fit_transform(X_tfidf)
X_svd_norm = X_svd / np.clip(np.linalg.norm(X_svd, axis=1, keepdims=True), 1e-9, None)

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer


def minmax(values):
    low, high = float(values.min()), float(values.max())
    if high - low < 1e-9:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def coverage(query, text):
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    return len(query_tokens & text_tokens) / max(len(query_tokens), 1)


def tfidf_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    return (X_tfidf @ query_vector.T).toarray().ravel()


def vector_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    query_svd = svd.transform(query_vector).ravel()
    query_norm = query_svd / max(float(np.linalg.norm(query_svd)), 1e-9)
    return X_svd_norm @ query_norm


def hybrid_scores(query, alpha=0.55):
    lexical = 0.5 * minmax(tfidf_scores(query)) + 0.5 * minmax(bm25.scores(query))
    vector = minmax(vector_scores(query))
    return alpha * lexical + (1 - alpha) * vector


def search(query, k=5, mode="hybrid", alpha=0.55, rerank=True):
    if mode == "tfidf":
        scores = tfidf_scores(query)
    elif mode == "bm25":
        scores = bm25.scores(query)
    elif mode == "vector":
        scores = vector_scores(query)
    else:
        scores = hybrid_scores(query, alpha)

    candidates = np.argsort(-scores)[: max(k, 12)]
    rows = []
    for index in candidates:
        score = float(scores[index])
        if rerank and mode == "hybrid":
            row = chunks.iloc[index]
            score += 0.08 * coverage(query, row["search_text"])
            if set(tokenize(query)) & set(tokenize(row["heading"])):
                score += 0.05
        rows.append((index, score))
    rows.sort(key=lambda item: -item[1])

    selected = [index for index, _ in rows[:k]]
    result = chunks.iloc[selected].copy()
    result["score"] = [score for _, score in rows[:k]]
    result["rank"] = range(1, len(result) + 1)
    return result[["rank", "chunk_id", "doc_id", "title", "heading", "text", "score"]]


print("片段数:", len(chunks))
print("词项数:", X_tfidf.shape[1])
print("SVD 分量:", X_svd.shape[1])
print("保留方差: {:.2%}".format(svd.explained_variance_ratio_.sum()))


queries = pd.read_csv(data_path("eval_queries.csv"))
print("评估问题数:", len(queries))
display(queries.head())


def evaluate_retrieval(search_fn, k=3):
    rows = []
    for _, item in queries.iterrows():
        start = time.perf_counter()
        result = search_fn(item["query"], k)
        latency = (time.perf_counter() - start) * 1000
        found = list(result["doc_id"])
        reciprocal_rank = 0.0
        for rank, doc_id in enumerate(found, 1):
            if doc_id == item["relevant_doc"]:
                reciprocal_rank = 1.0 / rank
                break
        top = result.iloc[0]
        cited_text = top["heading"] + "\n" + top["text"]
        rows.append(
            {
                "hit1": int(top["doc_id"] == item["relevant_doc"]),
                "hit3": int(item["relevant_doc"] in found),
                "rr": reciprocal_rank,
                "citation": int(item["key_phrase"] in cited_text),
                "latency_ms": latency,
            }
        )
    return pd.DataFrame(rows)


methods = {
    "TF-IDF": lambda query, k: search(query, k, mode="tfidf"),
    "BM25": lambda query, k: search(query, k, mode="bm25"),
    "SVD 向量": lambda query, k: search(query, k, mode="vector"),
    "混合 + 重排": lambda query, k: search(query, k, mode="hybrid"),
}
frames = {name: evaluate_retrieval(fn) for name, fn in methods.items()}
metrics = pd.DataFrame(
    [
        {
            "方法": name,
            "Hit@1": round(frame["hit1"].mean(), 3),
            "Hit@3": round(frame["hit3"].mean(), 3),
            "MRR": round(frame["rr"].mean(), 3),
            "引用命中": round(frame["citation"].mean(), 3),
            "平均延迟(ms)": round(frame["latency_ms"].mean(), 2),
        }
        for name, frame in frames.items()
    ]
)
display(metrics)


query = "发票怎么申请"
result = search(query, k=5, mode="hybrid")
display(result[["rank", "chunk_id", "heading", "score"]])
print("查询词覆盖度:", round(coverage(query, result.iloc[0]["text"]), 3))
print("标题是否命中:", bool(set(tokenize(query)) & set(tokenize(result.iloc[0]["heading"]))))


names = metrics["方法"].tolist()
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

x = np.arange(len(names))
width = 0.26
axes[0].bar(x - width, metrics["Hit@1"], width, label="Hit@1", color="#4C78A8")
axes[0].bar(x, metrics["Hit@3"], width, label="Hit@3", color="#54A24B")
axes[0].bar(x + width, metrics["引用命中"], width, label="引用命中", color="#F58518")
axes[0].set_xticks(x)
axes[0].set_xticklabels(names, rotation=20, ha="right")
axes[0].set_ylim(0, 1.05)
axes[0].set_ylabel("比例")
axes[0].set_title("不同检索方法的命中情况")
axes[0].legend(fontsize=8)

axes[1].barh(names, metrics["平均延迟(ms)"], color="#9DB4C8")
for index, value in enumerate(metrics["平均延迟(ms)"]):
    axes[1].text(value + 0.1, index, f"{value:.1f}", va="center", fontsize=9)
axes[1].set_xlabel("毫秒")
axes[1].set_title("单次查询平均延迟")

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "hybrid-metrics.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "hybrid-metrics.png")))
plt.close(fig)

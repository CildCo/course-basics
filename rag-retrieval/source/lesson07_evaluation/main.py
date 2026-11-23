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

def evaluate_retrieval(search_fn, queries, k=3):
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
                "id": item["id"],
                "query": item["query"],
                "query_type": item["query_type"],
                "expected": item["relevant_doc"],
                "top1": top["doc_id"],
                "hit1": int(top["doc_id"] == item["relevant_doc"]),
                "hit3": int(item["relevant_doc"] in found),
                "rr": reciprocal_rank,
                "citation": int(item["key_phrase"] in cited_text),
                "latency_ms": latency,
            }
        )
    return pd.DataFrame(rows)

def clean_markdown(text):
    text = str(text).replace("**", "").replace("`", "")
    return re.sub(r"^\s*(?:\d+\.|[-*])\s*", "", text, flags=re.M)


def split_sentences(text):
    parts = re.split(r"(?<=[。！？；])|\n+", clean_markdown(text))
    return [part.strip() for part in parts if part.strip()]


def select_sentences(query, text, max_sentences=2):
    query_tokens = tokenize(query)
    total_weight = sum(IDF.get(token, 1.0) for token in query_tokens) or 1.0
    items = []
    for index, sentence in enumerate(split_sentences(text)):
        sentence_tokens = set(tokenize(sentence))
        weight = sum(
            IDF.get(token, 1.0) for token in query_tokens if token in sentence_tokens
        )
        items.append((weight / total_weight, -index, sentence, index))
    items.sort(reverse=True)
    chosen = [(score, sentence, index) for score, _, sentence, index in items if score > 0]
    chosen = chosen[:max_sentences]
    if not chosen:
        return split_sentences(text)[:1]
    chosen.sort(key=lambda row: row[2])
    return [sentence for _, sentence, _ in chosen]


def coverage(query, text):
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    return len(query_tokens & text_tokens) / max(len(query_tokens), 1)


def build_answer(query, results):
    top = results.iloc[0]
    if coverage(query, top["text"]) < 0.08:
        return "没有找到足够证据，建议换一个问法或补充文档。"
    sentences = select_sentences(query, top["text"], 2)
    return (
        f"根据《{top['title']}》的“{top['heading']}”一节："
        + " ".join(sentences)
        + " [1]"
    )

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer


def minmax(values):
    low, high = float(values.min()), float(values.max())
    if high - low < 1e-9:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def tfidf_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    return (X_tfidf @ query_vector.T).toarray().ravel()


def vector_scores(query):
    query_vector = vectorizer.transform([" ".join(tokenize(query))])
    query_svd = svd.transform(query_vector).ravel()
    query_norm = query_svd / max(float(np.linalg.norm(query_svd)), 1e-9)
    return X_svd_norm @ query_norm


def search(query, k=3, alpha=0.55):
    lexical = 0.5 * minmax(tfidf_scores(query)) + 0.5 * minmax(bm25.scores(query))
    vector = minmax(vector_scores(query))
    scores = alpha * lexical + (1 - alpha) * vector

    candidates = np.argsort(-scores)[: max(k, 12)]
    rows = []
    for index in candidates:
        score = float(scores[index])
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
    result["citation_text"] = result["heading"] + "\n" + result["text"]
    return result[["rank", "chunk_id", "doc_id", "title", "heading", "text", "citation_text", "score"]]


IDF = dict(zip(vectorizer.get_feature_names_out(), vectorizer.idf_))
queries = pd.read_csv(data_path("eval_queries.csv"))
print("片段数:", len(chunks))
print("问题数:", len(queries))


def evaluate_answers(search_fn, k=3):
    rows = []
    for _, item in queries.iterrows():
        start = time.perf_counter()
        result = search_fn(item["query"], k)
        latency = (time.perf_counter() - start) * 1000
        answer = build_answer(item["query"], result)
        found = list(result["doc_id"])
        reciprocal_rank = 0.0
        for rank, doc_id in enumerate(found, 1):
            if doc_id == item["relevant_doc"]:
                reciprocal_rank = 1.0 / rank
                break
        top = result.iloc[0]
        rows.append(
            {
                "id": item["id"],
                "query": item["query"],
                "type": item["query_type"],
                "expected": item["relevant_doc"],
                "top1": top["doc_id"],
                "hit1": int(top["doc_id"] == item["relevant_doc"]),
                "hit3": int(item["relevant_doc"] in found),
                "rr": reciprocal_rank,
                "citation": int(item["key_phrase"] in top["citation_text"]),
                "answer_citation": int(item["key_phrase"] in answer),
                "latency_ms": latency,
            }
        )
    return pd.DataFrame(rows)


results = evaluate_answers(lambda query, k: search(query, k), k=3)
summary = {
    "Hit@1": results["hit1"].mean(),
    "Hit@3": results["hit3"].mean(),
    "MRR": results["rr"].mean(),
    "引用准确率": results["citation"].mean(),
    "答案引用准确率": results["answer_citation"].mean(),
    "平均延迟(ms)": results["latency_ms"].mean(),
    "P95 延迟(ms)": results["latency_ms"].quantile(0.95),
}
for name, value in summary.items():
    if name.endswith("(ms)"):
        print(f"{name}: {value:.2f}")
    else:
        print(f"{name}: {value:.3f}")

display(results[["id", "query", "expected", "top1", "hit1", "hit3", "citation", "answer_citation", "latency_ms"]])


fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

metric_names = ["Hit@1", "Hit@3", "MRR", "引用准确率", "答案引用准确率"]
metric_values = [
    summary["Hit@1"],
    summary["Hit@3"],
    summary["MRR"],
    summary["引用准确率"],
    summary["答案引用准确率"],
]
axes[0].bar(metric_names, metric_values, color=["#4C78A8", "#54A24B", "#72B7B2", "#F58518", "#E45756"])
axes[0].set_ylim(0, 1.05)
axes[0].set_ylabel("比例")
axes[0].set_title("检索与引用指标")
axes[0].tick_params(axis="x", rotation=20)

latencies = results["latency_ms"].to_numpy()
axes[1].hist(latencies, bins=8, color="#9DB4C8", edgecolor="white")
axes[1].axvline(summary["平均延迟(ms)"], color="#C44E52", linestyle="--", label="平均")
axes[1].axvline(summary["P95 延迟(ms)"], color="#F58518", linestyle=":", label="P95")
axes[1].set_xlabel("毫秒")
axes[1].set_ylabel("问题数")
axes[1].set_title("单次查询延迟分布")
axes[1].legend(fontsize=8)

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "evaluation-metrics.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "evaluation-metrics.png")))
plt.close(fig)


errors = results[(results["hit3"] == 0) | (results["citation"] == 0)].copy()
print("需要分析的样本数:", len(errors))
display(errors[["id", "query", "expected", "top1", "hit1", "hit3", "citation", "answer_citation"]])

for _, row in errors.iterrows():
    result = search(row["query"], k=3)
    print("问题：", row["query"], "| 期望：", row["expected"], "| 实际：", row["top1"])
    display(result[["rank", "chunk_id", "heading", "score"]])

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
    return result[["rank", "chunk_id", "doc_id", "title", "heading", "text", "score"]]


IDF = dict(zip(vectorizer.get_feature_names_out(), vectorizer.idf_))
print("片段数:", len(chunks))
print("IDF 词项数:", len(IDF))


examples = [
    "退款多久能到账",
    "API 请求头怎么带令牌",
    "怎么保证客户资料不外泄",
    "多人协作编辑怎么处理冲突",
]

for query in examples:
    results = search(query, k=3)
    answer = build_answer(query, results)
    top = results.iloc[0]
    print("问题：", query)
    print("回答：", answer)
    print("出处：", f"[1] {top['doc_id']} · {top['heading']}")
    print("-" * 60)


unknown = [
    "火星基地氧气循环设计",
    "热带雨林鸟类迁徙",
]

for query in unknown:
    results = search(query, k=3)
    answer = build_answer(query, results)
    print("问题：", query)
    print("回答：", answer)
    print("最高覆盖度:", round(coverage(query, results.iloc[0]["text"]), 3))
    print("-" * 60)

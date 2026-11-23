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


def minmax(values):
    low, high = float(values.min()), float(values.max())
    if high - low < 1e-9:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def coverage(query, text):
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    return len(query_tokens & text_tokens) / max(len(query_tokens), 1)


def clean_markdown(text):
    text = str(text).replace("**", "").replace("`", "")
    return re.sub(r"^\s*(?:\d+\.|[-*])\s*", "", text, flags=re.M)


def split_sentences(text):
    parts = re.split(r"(?<=[。！？；])|\n+", clean_markdown(text))
    return [part.strip() for part in parts if part.strip()]


class KnowledgeBaseRetriever:
    def __init__(self, docs_dir, max_chars=360, overlap=60, alpha=0.55, min_coverage=0.08):
        self.docs_dir = Path(docs_dir)
        self.max_chars = max_chars
        self.overlap = overlap
        self.alpha = alpha
        self.min_coverage = min_coverage
        self.docs = []
        self.chunks = None
        self.vectorizer = None
        self.x_tfidf = None
        self.svd = None
        self.x_svd_norm = None
        self.bm25 = None
        self.idf = {}

    def build(self):
        self.docs = load_documents(self.docs_dir)
        self.chunks = split_documents(self.docs, self.max_chars, self.overlap)
        corpus = [" ".join(tokenize(text)) for text in self.chunks["search_text"]]
        self.vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\S+", lowercase=False, sublinear_tf=True
        )
        self.x_tfidf = self.vectorizer.fit_transform(corpus)
        self.bm25 = BM25([tokenize(text) for text in self.chunks["search_text"]])
        components = min(48, self.x_tfidf.shape[0] - 1, self.x_tfidf.shape[1] - 1)
        self.svd = TruncatedSVD(n_components=components, random_state=42)
        matrix = self.svd.fit_transform(self.x_tfidf)
        self.x_svd_norm = matrix / np.clip(
            np.linalg.norm(matrix, axis=1, keepdims=True), 1e-9, None
        )
        self.idf = dict(zip(self.vectorizer.get_feature_names_out(), self.vectorizer.idf_))
        return self

    def _scores(self, query):
        query_vector = self.vectorizer.transform([" ".join(tokenize(query))])
        tfidf = (self.x_tfidf @ query_vector.T).toarray().ravel()
        bm25 = self.bm25.scores(query)
        query_svd = self.svd.transform(query_vector).ravel()
        query_norm = query_svd / max(float(np.linalg.norm(query_svd)), 1e-9)
        vector = self.x_svd_norm @ query_norm
        lexical = 0.5 * minmax(tfidf) + 0.5 * minmax(bm25)
        scores = self.alpha * lexical + (1 - self.alpha) * minmax(vector)
        return scores

    def search(self, query, k=3):
        scores = self._scores(query)
        candidates = np.argsort(-scores)[: max(k, 12)]
        rows = []
        for index in candidates:
            score = float(scores[index])
            row = self.chunks.iloc[index]
            score += 0.08 * coverage(query, row["search_text"])
            if set(tokenize(query)) & set(tokenize(row["heading"])):
                score += 0.05
            rows.append((index, score))
        rows.sort(key=lambda item: -item[1])

        selected = [index for index, _ in rows[:k]]
        result = self.chunks.iloc[selected].copy()
        result["score"] = [score for _, score in rows[:k]]
        result["rank"] = range(1, len(result) + 1)
        result["citation_text"] = result["heading"] + "\n" + result["text"]
        return result[
            ["rank", "chunk_id", "doc_id", "title", "heading", "text", "citation_text", "score"]
        ]

    def _select_sentences(self, query, text, max_sentences=2):
        query_tokens = tokenize(query)
        total_weight = sum(self.idf.get(token, 1.0) for token in query_tokens) or 1.0
        items = []
        for index, sentence in enumerate(split_sentences(text)):
            sentence_tokens = set(tokenize(sentence))
            weight = sum(
                self.idf.get(token, 1.0)
                for token in query_tokens
                if token in sentence_tokens
            )
            items.append((weight / total_weight, -index, sentence, index))
        items.sort(reverse=True)
        chosen = [(score, sentence, index) for score, _, sentence, index in items if score > 0]
        chosen = chosen[:max_sentences]
        if not chosen:
            return split_sentences(text)[:1]
        chosen.sort(key=lambda row: row[2])
        return [sentence for _, sentence, _ in chosen]

    def answer(self, query, k=3):
        results = self.search(query, k)
        top = results.iloc[0]
        if coverage(query, top["text"]) < self.min_coverage:
            return "没有找到足够证据，建议换一个问法或补充文档。", results
        sentences = self._select_sentences(query, top["text"])
        text = (
            f"根据《{top['title']}》的“{top['heading']}”一节："
            + " ".join(sentences)
            + " [1]"
        )
        return text, results

    def evaluate(self, queries, k=3):
        rows = []
        for _, item in queries.iterrows():
            start = time.perf_counter()
            answer, result = self.answer(item["query"], k)
            latency = (time.perf_counter() - start) * 1000
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


retriever = KnowledgeBaseRetriever(data_path("docs")).build()
print("文档数:", len(retriever.docs))
print("片段数:", len(retriever.chunks))
print("词项数:", retriever.x_tfidf.shape[1])
print("SVD 分量:", retriever.x_svd_norm.shape[1])
print("保留方差: {:.2%}".format(retriever.svd.explained_variance_ratio_.sum()))
display(retriever.chunks.groupby("doc_id").agg(片段数=("chunk_id", "count"), 平均长度=("chars", "mean")).round(1))


demo_queries = [
    "团队版怎么收费",
    "怎么导入 Markdown 文档",
    "索引重建时提示文件格式不支持",
    "怎么保证客户资料不外泄",
    "火星基地氧气循环设计",
]

for query in demo_queries:
    answer, results = retriever.answer(query, k=3)
    top = results.iloc[0]
    print("问题：", query)
    print("回答：", answer)
    if answer.startswith("没有找到足够证据"):
        print("出处：未引用片段")
        print("检索最高分：", round(float(top["score"]), 3))
    else:
        print("出处：", f"[1] {top['doc_id']} · {top['heading']}")
        print("分数：", round(float(top["score"]), 3))
    print("-" * 60)


queries = pd.read_csv(data_path("eval_queries.csv"))
results = retriever.evaluate(queries, k=3)
results.to_csv(out / "eval_results.csv", index=False, encoding="utf-8-sig")

summary = {
    "问题数": len(results),
    "Hit@1": results["hit1"].mean(),
    "Hit@3": results["hit3"].mean(),
    "MRR": results["rr"].mean(),
    "引用准确率": results["citation"].mean(),
    "答案引用准确率": results["answer_citation"].mean(),
    "平均延迟(ms)": results["latency_ms"].mean(),
    "P95 延迟(ms)": results["latency_ms"].quantile(0.95),
}

by_type = results.groupby("type").agg(
    问题数=("id", "count"),
    Hit_at_1=("hit1", "mean"),
    Hit_at_3=("hit3", "mean"),
    引用准确率=("citation", "mean"),
).round(3)

print("总体指标")
for name, value in summary.items():
    if name == "问题数":
        print(f"  {name}: {int(value)}")
    elif name.endswith("(ms)"):
        print(f"  {name}: {value:.2f}")
    else:
        print(f"  {name}: {value:.3f}")

print("按问题类型")
display(by_type)
display(results[["id", "query", "expected", "top1", "hit1", "hit3", "citation", "answer_citation"]])


fig, axes = plt.subplots(2, 2, figsize=(11, 8))

metric_names = ["Hit@1", "Hit@3", "MRR", "引用准确率", "答案引用准确率"]
metric_values = [
    summary["Hit@1"],
    summary["Hit@3"],
    summary["MRR"],
    summary["引用准确率"],
    summary["答案引用准确率"],
]
axes[0, 0].bar(metric_names, metric_values, color=["#4C78A8", "#54A24B", "#72B7B2", "#F58518", "#E45756"])
axes[0, 0].set_ylim(0, 1.05)
axes[0, 0].set_title("检索与引用指标")
axes[0, 0].tick_params(axis="x", rotation=20)

axes[0, 1].hist(retriever.chunks["chars"], bins=12, color="#9DB4C8", edgecolor="white")
axes[0, 1].axvline(retriever.max_chars, color="#C44E52", linestyle="--", label="长度上限")
axes[0, 1].set_xlabel("片段字符数")
axes[0, 1].set_ylabel("片段数")
axes[0, 1].set_title("片段长度分布")
axes[0, 1].legend(fontsize=8)

axes[1, 0].bar(by_type.index, by_type["Hit_at_1"], color="#72B7B2")
axes[1, 0].set_ylim(0, 1.05)
axes[1, 0].set_ylabel("Hit@1")
axes[1, 0].set_title("按问题类型的命中率")
axes[1, 0].tick_params(axis="x", rotation=15)

axes[1, 1].plot(results["id"], results["latency_ms"], marker="o", ms=4, color="#4C78A8")
axes[1, 1].axhline(summary["平均延迟(ms)"], color="#C44E52", linestyle="--", label="平均")
axes[1, 1].axhline(summary["P95 延迟(ms)"], color="#F58518", linestyle=":", label="P95")
axes[1, 1].set_xlabel("问题 ID")
axes[1, 1].set_ylabel("毫秒")
axes[1, 1].set_title("逐题延迟")
axes[1, 1].legend(fontsize=8)
axes[1, 1].tick_params(axis="x", rotation=45)

for ax in axes.flat:
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "retrieval-dashboard.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "retrieval-dashboard.png")))
plt.close(fig)


errors = results[(results["hit3"] == 0) | (results["citation"] == 0)]
error_lines = []
for _, row in errors.iterrows():
    error_lines.append(
        f"- {row['id']} {row['query']}：期望 `{row['expected']}`，实际 `{row['top1']}`，"
        f"Hit@3={row['hit3']}，引用={row['citation']}"
    )
if not error_lines:
    error_lines = ["- 本次问题集没有出现命中或引用失败。"]

report = f"""# 本地知识库检索层评估报告

## 数据

- 文档数：{len(retriever.docs)}
- 片段数：{len(retriever.chunks)}
- 问题数：{summary["问题数"]}
- 切分参数：最大 {retriever.max_chars} 字符，重叠 {retriever.overlap} 字符
- 混合权重：词法 {retriever.alpha:.2f}，向量 {1 - retriever.alpha:.2f}

## 指标

| 指标 | 数值 |
| --- | --- |
| Hit@1 | {summary["Hit@1"]:.3f} |
| Hit@3 | {summary["Hit@3"]:.3f} |
| MRR | {summary["MRR"]:.3f} |
| 引用准确率 | {summary["引用准确率"]:.3f} |
| 答案引用准确率 | {summary["答案引用准确率"]:.3f} |
| 平均延迟 | {summary["平均延迟(ms)"]:.2f} ms |
| P95 延迟 | {summary["P95 延迟(ms)"]:.2f} ms |

## 错误样本

{chr(10).join(error_lines)}

## 结论

检索层已经能完成文档加载、切分、混合检索、重排和抽取式引用。生成层未接入大模型，回答直接来自原文句子；替换生成层时，应继续要求模型只使用检索片段并保留引用编号。

当前问题集规模较小，指标只代表这类文档和问法。扩充问题集、增加文档类型后，需要重新跑评估，并根据错误样本调整切分长度、融合权重和引用阈值。
"""
(out / "retrieval_report.md").write_text(report, encoding="utf-8")
print(report)

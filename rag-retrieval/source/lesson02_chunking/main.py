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

docs = load_documents(data_path("docs"))
chunks = split_documents(docs, max_chars=180, overlap=40)

summary = (
    chunks.groupby("doc_id")
    .agg(片段数=("chunk_id", "count"), 平均长度=("chars", "mean"), 最长=("chars", "max"))
    .round(1)
)
print("文档数:", len(docs))
print("片段数:", len(chunks))
print("片段平均长度:", round(chunks["chars"].mean(), 1))
print("最长片段:", int(chunks["chars"].max()))
display(summary)
display(chunks[["chunk_id", "doc_id", "heading", "chars"]].head(8))


def heading_only_chunks(docs):
    rows = []
    for doc in docs:
        for heading, body in parse_sections(doc["text"]):
            rows.append({"doc_id": doc["doc_id"], "heading": heading, "chars": len(body)})
    return pd.DataFrame(rows)


def paragraph_only_chunks(docs):
    rows = []
    for doc in docs:
        for heading, body in parse_sections(doc["text"]):
            for paragraph in re.split(r"\n\s*\n", body):
                paragraph = paragraph.strip()
                if paragraph:
                    rows.append(
                        {"doc_id": doc["doc_id"], "heading": heading, "chars": len(paragraph)}
                    )
    return pd.DataFrame(rows)


heading_df = heading_only_chunks(docs)
paragraph_df = paragraph_only_chunks(docs)
length_df = chunks[["doc_id", "heading", "chars"]]

compare = pd.DataFrame(
    [
        {
            "策略": "仅按标题",
            "片段数": len(heading_df),
            "平均长度": round(heading_df["chars"].mean(), 1),
            "最长片段": int(heading_df["chars"].max()),
        },
        {
            "策略": "仅按段落",
            "片段数": len(paragraph_df),
            "平均长度": round(paragraph_df["chars"].mean(), 1),
            "最长片段": int(paragraph_df["chars"].max()),
        },
        {
            "策略": "标题 + 段落 + 长度",
            "片段数": len(length_df),
            "平均长度": round(length_df["chars"].mean(), 1),
            "最长片段": int(length_df["chars"].max()),
        },
    ]
)
display(compare)


fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

axes[0].hist(
    [heading_df["chars"], paragraph_df["chars"], length_df["chars"]],
    bins=12,
    label=["仅按标题", "仅按段落", "标题 + 段落 + 长度"],
    color=["#9DB4C8", "#F2B880", "#4C78A8"],
    alpha=0.78,
)
axes[0].set_xlabel("片段字符数")
axes[0].set_ylabel("片段数量")
axes[0].set_title("三种切分策略的长度分布")
axes[0].legend(fontsize=8)

names = compare["策略"].tolist()
counts = compare["片段数"].tolist()
axes[1].barh(names, counts, color=["#9DB4C8", "#F2B880", "#4C78A8"])
for index, value in enumerate(counts):
    axes[1].text(value + 1, index, str(value), va="center", fontsize=9)
axes[1].set_xlabel("片段数量")
axes[1].set_title("片段数量对比")

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "chunk-strategies.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "chunk-strategies.png")))
plt.close(fig)


sample = chunks.groupby("doc_id").head(1)[["chunk_id", "doc_id", "heading", "chars", "text"]].head(6).copy()
sample["text"] = sample["text"].str.replace("\n", " ").str.slice(0, 60) + "…"
display(sample)

print("每篇文档的片段数：")
print(chunks.groupby("doc_id")["chunk_id"].count().to_string())

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

docs_dir = data_path("docs")
rows = []
for path in sorted(docs_dir.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    title = path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    headings = re.findall(r"^## (.+)$", text, flags=re.M)
    rows.append(
        {
            "doc_id": path.stem,
            "title": title,
            "chars": len(text),
            "sections": len(headings),
        }
    )

docs = pd.DataFrame(rows)
print("文档数:", len(docs))
print("总字符:", int(docs["chars"].sum()))
print("二级标题数:", int(docs["sections"].sum()))
print("平均每篇字符:", int(docs["chars"].mean()))
display(docs)


from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(10, 3.8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis("off")

boxes = [
    (0.3, "用户问题", "输入"),
    (2.4, "检索层\n切片 / 打分 / 重排", "本课重点"),
    (4.8, "生成层\n组织语言", "可替换"),
    (7.2, "引用层\n标注出处", "可核对"),
]
for x, title, note in boxes:
    rect = FancyBboxPatch(
        (x, 2.2),
        1.7,
        1.2,
        boxstyle="round,pad=0.06,rounding_size=0.12",
        linewidth=1.2,
        edgecolor="#4C6E91",
        facecolor="#EAF1F7",
    )
    ax.add_patch(rect)
    ax.text(x + 0.85, 2.98, title, ha="center", va="center", fontsize=11,
            weight="bold", color="#1F3A52")
    ax.text(x + 0.85, 2.48, note, ha="center", va="center", fontsize=9, color="#5A6B7B")

for start, end in [(2.0, 2.4), (4.1, 4.8), (6.5, 7.2)]:
    ax.annotate(
        "",
        xy=(end, 2.8),
        xytext=(start, 2.8),
        arrowprops=dict(arrowstyle="->", lw=1.4, color="#4C6E91"),
    )

ax.text(5.0, 0.7, "检索层只负责找到证据并给出处，不负责编造答案",
        ha="center", fontsize=10, color="#7A4E2D")
ax.text(5.0, 1.2, "pipeline: question -> retrieve -> generate -> cite",
        ha="center", fontsize=9, color="#8796A5")

fig.savefig(out / "rag-pipeline.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "rag-pipeline.png")))
plt.close(fig)

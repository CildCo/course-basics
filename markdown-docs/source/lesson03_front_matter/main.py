from pathlib import Path
import json
import yaml

def data_path(name):
    here = Path.cwd().resolve()
    for base in [here, *here.parents]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"找不到 assets/{name}")

output_dir = Path.cwd() / "output"
output_dir.mkdir(exist_ok=True)
docs_dir = data_path("docs")


def split_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    meta = yaml.safe_load(raw) or {}
    if not isinstance(meta, dict):
        raise ValueError("front matter 必须是键值对")
    return meta, text[end + 4:].lstrip("\n")


REQUIRED = {"title": str, "nav": str, "order": int, "summary": str}


def validate(meta):
    problems = []
    for key, expected in REQUIRED.items():
        if key not in meta:
            problems.append(f"缺少 {key}")
        elif not isinstance(meta[key], expected) or isinstance(meta[key], bool):
            problems.append(f"{key} 应为 {expected.__name__}")
    tags = meta.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        problems.append("tags 应为字符串列表")
    return problems


meta, body = split_front_matter((docs_dir / "README.md").read_text(encoding="utf-8"))
print("字段:", sorted(meta))
print("order 类型:", type(meta["order"]).__name__)
print("tags 类型:", type(meta["tags"]).__name__)
print("正文开头:", body.splitlines()[0])


records = []
problems = []
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    meta, body = split_front_matter(path.read_text(encoding="utf-8"))
    issues = validate(meta)
    problems.extend((rel, issue) for issue in issues)
    records.append(
        {
            "file": rel,
            "title": meta.get("title", ""),
            "nav": meta.get("nav", ""),
            "order": meta.get("order", 0),
            "summary": meta.get("summary", ""),
            "tags": meta.get("tags", []),
            "chars": len(body),
        }
    )

records.sort(key=lambda item: item["order"])

print(f"{'文件':26}{'order':>6}{'nav':>12}{'tags':>14}")
for item in records:
    print(f"{item['file']:26}{item['order']:>6}{item['nav']:>12}{len(item['tags']):>14}")

print()
print("校验问题:", len(problems))
for rel, issue in problems:
    print("-", rel, issue)


(output_dir / "metadata.json").write_text(
    json.dumps(records, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print("索引文件:", output_dir / "metadata.json")
print("记录数量:", len(records))
print("排序后的标题:", [item["title"] for item in records])
print()
print(json.dumps(records[0], ensure_ascii=False, indent=2))


bad = """---
title: 缺少字段
order: 三
tags: 文档
---
正文
"""

meta, body = split_front_matter(bad)
print("解析结果:", meta)
print("校验问题:")
for issue in validate(meta):
    print("-", issue)

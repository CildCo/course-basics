from pathlib import Path
import re

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
print("文档目录:", docs_dir)
print("文档数量:", len(list(docs_dir.rglob("*.md"))))


def read_doc(path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    return text.lstrip("\n")


def without_code(text):
    lines = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            lines.append(line)
    return "\n".join(lines)


def headings(text):
    found = []
    for line in without_code(text).splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            found.append((len(match.group(1)), match.group(2).strip()))
    return found


def stats(text):
    body = without_code(text)
    plain = re.sub(r"`[^`]*`", "", body)
    paragraphs = [
        block
        for block in re.split(r"\n\s*\n", body)
        if block.strip() and not block.lstrip().startswith(("#", "-", "*", ">", "|", "1."))
    ]
    return {
        "headings": len(headings(text)),
        "paragraphs": len(paragraphs),
        "list_items": len(re.findall(r"^\s*(?:[-*+]|\d+\.)\s+", body, re.M)),
        "links": len(re.findall(r"(?<!!)\[[^\]]+\]\([^)]+\)", plain)),
        "tables": len(re.findall(r"^\|.+\|\s*$", body, re.M)),
        "fences": text.count("```") // 2,
    }


rows = []
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    rows.append((rel, stats(path.read_text(encoding="utf-8"))))

print(f"{'文档':26}{'标题':>6}{'段落':>6}{'列表':>6}{'链接':>6}{'代码块':>7}{'表格行':>7}")
for rel, item in rows:
    print(
        f"{rel:26}{item['headings']:>6}{item['paragraphs']:>6}"
        f"{item['list_items']:>6}{item['links']:>6}{item['fences']:>7}{item['tables']:>7}"
    )

print()
print("合计文档:", len(rows))
print("合计标题:", sum(item["headings"] for _, item in rows))


issues = []
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    print(rel)
    previous = 0
    for level, title in headings(read_doc(path)):
        print("  " * (level - 1) + f"{'#' * level} {title}")
        if previous and level > previous + 1:
            issues.append(f"{rel}: 「{title}」从 h{previous} 跳到 h{level}")
        previous = level

print()
print("跳级问题:", len(issues))
for issue in issues:
    print("-", issue)


print(f"{'文档':26}{'反引号行':>8}{'状态':>8}")
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("```"))
    status = "闭合" if count % 2 == 0 else "未闭合"
    print(f"{rel:26}{count:>8}{status:>8}")

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


def slugify(text):
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w一-鿿\- ]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def anchors_for(text):
    seen = {}
    result = []
    for level, title in headings(text):
        base = slugify(title)
        count = seen.get(base, 0)
        anchor = base if count == 0 else f"{base}_{count}"
        seen[base] = count + 1
        result.append((level, title, anchor))
    return result


print("中文标题锚点:", slugify("目录、锚点与交叉引用"))
print("中英混排锚点:", slugify("front matter 与元数据"))
print("重复标题测试:", [anchor for _, _, anchor in anchors_for("# 重复\n\n## 重复\n\n## 重复")])


target = data_path("docs/reference/syntax.md")
entries = anchors_for(read_doc(target))

lines = ["## 语法速查目录", ""]
for level, title, anchor in entries:
    if level < 2:
        continue
    indent = "  " * (level - 2)
    lines.append(f"{indent}- [{title}](#{anchor})")

toc = "\n".join(lines) + "\n"
(output_dir / "toc.md").write_text(toc, encoding="utf-8")

print(toc)
print("已写入:", output_dir / "toc.md")


link_re = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?")


def without_inline_code(text):
    return re.sub(r"`[^`]*`", "", text)


def case_issue(file_part):
    for part in Path(file_part).parts:
        if part in {"..", "."} or part == "README.md":
            continue
        if part != part.lower():
            return f"路径含大写：{part}"
    return ""


def check_links(path, docs_root):
    text = without_inline_code(without_code(read_doc(path)))
    problems = []
    checked = 0
    anchors_cache = {}

    for label, target in link_re.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        checked += 1
        file_part, _, anchor = target.partition("#")
        target_path = path if not file_part else (path.parent / file_part)
        if file_part:
            target_path = target_path.resolve()
            try:
                target_path.relative_to(docs_root.resolve())
            except ValueError:
                problems.append(f"链接越出 docs 目录：{target}")
                continue
            if not target_path.exists():
                problems.append(f"找不到文件：{target}")
                continue
            issue = case_issue(file_part)
            if issue:
                problems.append(f"{issue}（{target}）")
        if anchor:
            if target_path not in anchors_cache:
                anchors_cache[target_path] = {a for _, _, a in anchors_for(read_doc(target_path))}
            if anchor not in anchors_cache[target_path]:
                problems.append(f"锚点不存在：{target}")
    return checked, problems


total = 0
all_problems = []
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    checked, problems = check_links(path, docs_dir)
    total += checked
    all_problems.extend((rel, problem) for problem in problems)
    status = "通过" if not problems else f"{len(problems)} 个问题"
    print(f"{rel:26}{checked:>3} 个链接  {status}")

print()
print("检查链接合计:", total)
print("问题合计:", len(all_problems))
for rel, problem in all_problems:
    print("-", rel, problem)

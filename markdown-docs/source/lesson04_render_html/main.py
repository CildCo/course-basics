from pathlib import Path
import re
import markdown

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
    return {}, text[end + 4:].lstrip("\n")


def slugify(value, separator="-"):
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = value.strip().lower()
    value = re.sub(r"[^\w一-鿿\- ]", "", value)
    value = re.sub(r"\s+", separator, value)
    return value.strip(separator)


def render_markdown(text):
    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": slugify}},
    )
    html = md.convert(text)
    return html, md.toc_tokens


def flatten_toc(tokens):
    result = []
    for token in tokens:
        result.append(token)
        result.extend(flatten_toc(token.get("children") or []))
    return result


print("markdown 版本:", markdown.__version__)


source = "## 中文标题\n\n## front matter 与元数据"

default_md = markdown.Markdown(extensions=["toc"])
default_html = default_md.convert(source)

custom_html, tokens = render_markdown(source)

print("默认渲染:")
for line in default_html.splitlines():
    if line.startswith("<h2"):
        print(" ", line)
print("自定义渲染:")
for line in custom_html.splitlines():
    if line.startswith("<h2"):
        print(" ", line)
print("目录节点:", [(token["level"], token["id"]) for token in tokens])


path = data_path("docs/reference/syntax.md")
meta, body = split_front_matter(path.read_text(encoding="utf-8"))
html, toc = render_markdown(body)
flat = flatten_toc(toc)

print("源文件:", path.name)
print("HTML 长度:", len(html))
print("标题数量:", len(flat))
print("包含表格:", "<table>" in html)
print("包含代码块:", "<pre>" in html)
print("包含二级标题:", "<h2" in html)
print("标题 id:", [token["id"] for token in flat])


css = """
body { margin: 0; background: #f7f6f2; color: #222; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
main { max-width: 760px; margin: 40px auto; padding: 32px 40px; background: #fff; border: 1px solid #e6e2d8; border-radius: 10px; line-height: 1.8; }
h1, h2, h3 { line-height: 1.35; color: #1f3b34; }
h2 { margin-top: 1.8em; border-bottom: 1px solid #ece7dc; padding-bottom: 6px; }
code { background: #f1eee6; padding: 2px 5px; border-radius: 4px; }
pre { background: #1f2b28; color: #f3f0e8; padding: 16px; border-radius: 8px; overflow-x: auto; }
pre code { background: transparent; padding: 0; color: inherit; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; }
th, td { border: 1px solid #ddd6c8; padding: 8px 10px; text-align: left; }
th { background: #f3f0e8; }
blockquote { margin: 16px 0; padding: 8px 16px; border-left: 3px solid #7aa28f; background: #f6f8f5; }
a { color: #2f6b55; }
"""

page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>语法速查 · 预览</title>
  <style>{css}</style>
</head>
<body>
  <main>{html}</main>
</body>
</html>
"""

preview = output_dir / "preview.html"
preview.write_text(page, encoding="utf-8")

print("预览文件:", preview)
print("文件大小:", len(page.encode("utf-8")), "字节")
print("外部样式:", len(re.findall(r'<link[^>]+https?://', page)))
print("外部脚本:", len(re.findall(r'<script[^>]+https?://', page)))

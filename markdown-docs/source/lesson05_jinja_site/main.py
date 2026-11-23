from pathlib import Path
import re

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

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
site_dir = output_dir / "site5"


def split_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = yaml.safe_load(text[3:end].strip()) or {}
    return meta, text[end + 4:].lstrip("\n")


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
    return md.convert(text)


def to_output(rel):
    if rel == "README.md":
        return "index.html"
    if rel.endswith("/README.md"):
        return rel[:-9] + "index.html"
    return rel[:-3] + ".html"


def rewrite_html_links(html):
    def replace(match):
        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return match.group(0)
        path, sep, anchor = target.partition("#")
        if path.endswith(".md"):
            if path == "README.md":
                path = "index.html"
            elif path.endswith("/README.md"):
                path = path[:-9] + "index.html"
            else:
                path = path[:-3] + ".html"
        return f'href="{path}{sep}{anchor}"'

    return re.sub(r'href="([^"]+)"', replace, html)


print("文档目录:", docs_dir)
print("站点目录:", site_dir)


template_text = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if title == site_name %}{{ site_name }}{% else %}{{ title }} · {{ site_name }}{% endif %}</title>
  <link rel="stylesheet" href="{{ root }}assets/style.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{{ root }}index.html">{{ site_name }}</a>
    <span class="tagline">{{ tagline }}</span>
  </header>
  <div class="shell">
    <nav class="side">
      {% for item in nav %}
      <a href="{{ root }}{{ item.href }}">{{ item.nav }}</a>
      {% endfor %}
    </nav>
    <main class="content">
      <article>{{ content|safe }}</article>
    </main>
  </div>
</body>
</html>
"""

css_text = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; background: #f6f5f0; color: #24211c; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; line-height: 1.8; }
.topbar { display: flex; align-items: baseline; gap: 16px; padding: 18px 32px; background: #20342f; color: #f4f1e8; }
.brand { color: #f4f1e8; font-weight: 700; text-decoration: none; letter-spacing: 0.02em; }
.tagline { color: #a9c2b7; font-size: 13px; }
.shell { display: grid; grid-template-columns: 188px minmax(0, 760px); gap: 32px; max-width: 1040px; margin: 32px auto; padding: 0 24px; }
.side { position: sticky; top: 24px; align-self: start; display: flex; flex-direction: column; gap: 4px; }
.side a { padding: 7px 10px; border-radius: 6px; color: #3c4a44; text-decoration: none; font-size: 14px; }
.side a:hover { background: #e8e4d9; }
.content { background: #fff; border: 1px solid #e5e0d4; border-radius: 10px; padding: 32px 40px; min-width: 0; }
h1, h2, h3 { color: #1d3a32; line-height: 1.35; }
h2 { margin-top: 1.9em; padding-bottom: 6px; border-bottom: 1px solid #ece7db; }
code { background: #f1eee6; padding: 2px 5px; border-radius: 4px; font-size: 0.92em; }
pre { background: #1f2b28; color: #f2efe7; padding: 16px; border-radius: 8px; overflow-x: auto; }
pre code { background: transparent; padding: 0; color: inherit; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; }
th, td { border: 1px solid #ddd6c8; padding: 8px 10px; text-align: left; }
th { background: #f3f0e8; }
blockquote { margin: 16px 0; padding: 8px 16px; border-left: 3px solid #7aa28f; background: #f5f8f4; }
a { color: #2f6b55; }
@media (max-width: 760px) { .shell { grid-template-columns: 1fr; } .side { position: static; flex-direction: row; flex-wrap: wrap; } .content { padding: 24px; } }
"""

templates_dir = output_dir / "templates"
templates_dir.mkdir(exist_ok=True)
(templates_dir / "base.html").write_text(template_text, encoding="utf-8")

if site_dir.exists():
    for path in sorted(site_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()

(site_dir / "assets").mkdir(parents=True, exist_ok=True)
(site_dir / "assets" / "style.css").write_text(css_text, encoding="utf-8")

env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
template = env.get_template("base.html")
print("模板已写入:", templates_dir / "base.html")
print("样式已写入:", site_dir / "assets" / "style.css")


pages = []
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    meta, body = split_front_matter(path.read_text(encoding="utf-8"))
    pages.append({"rel": rel, "output": to_output(rel), "meta": meta, "body": body})

pages.sort(key=lambda item: item["meta"]["order"])
nav = [{"nav": item["meta"]["nav"], "href": item["output"]} for item in pages]

for page in pages:
    html = render_markdown(page["body"])
    html = rewrite_html_links(html)
    root = "../" * page["output"].count("/")
    rendered = template.render(
        title=page["meta"]["title"],
        site_name="课程文档站",
        tagline="Markdown 与文档工程示例",
        root=root,
        nav=nav,
        content=html,
    )
    target = site_dir / page["output"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print("生成:", page["output"], "| 标题:", page["meta"]["title"])

print()
print("页面数量:", len(pages))
print("导航顺序:", [item["nav"] for item in nav])


missing = []
checked = 0
for page in pages:
    html = (site_dir / page["output"]).read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("http://", "https://", "#")):
            continue
        checked += 1
        target = (site_dir / page["output"]).parent / href.partition("#")[0]
        if not target.exists():
            missing.append(f"{page['output']} -> {href}")

print("检查 href:", checked)
print("缺失目标:", len(missing))
for item in missing:
    print("-", item)
print("站点入口:", site_dir / "index.html")
print("入口大小:", (site_dir / "index.html").stat().st_size, "字节")

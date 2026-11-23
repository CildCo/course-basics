from pathlib import Path
import posixpath
import re
import shutil

import markdown
import yaml
from jinja2 import Environment, DictLoader

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
site_dir = output_dir / "site"


def split_front_matter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    meta = yaml.safe_load(text[3:end].strip()) or {}
    if not isinstance(meta, dict):
        raise ValueError("front matter 必须是键值对")
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
    html = md.convert(text)
    return html, md.toc_tokens


def flatten_toc(tokens):
    result = []
    for token in tokens:
        if token["level"] >= 2:
            result.append({"level": token["level"], "id": token["id"], "name": token["name"]})
        result.extend(flatten_toc(token.get("children") or []))
    return result


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


print("准备生成站点:", site_dir)


pages = []
for path in sorted(docs_dir.rglob("*.md")):
    rel = path.relative_to(docs_dir).as_posix()
    meta, body = split_front_matter(path.read_text(encoding="utf-8"))
    for key in ("title", "nav", "order", "summary"):
        if key not in meta:
            raise ValueError(f"{rel} 缺少字段 {key}")
    pages.append(
        {
            "rel": rel,
            "output": to_output(rel),
            "meta": meta,
            "body": body,
        }
    )

pages.sort(key=lambda item: item["meta"]["order"])
print(f"{'源文件':26}{'输出':22}{'order':>6}  nav")
for page in pages:
    print(f"{page['rel']:26}{page['output']:22}{page['meta']['order']:>6}  {page['meta']['nav']}")


BASE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if meta.title == site_name %}{{ site_name }}{% else %}{{ meta.title }} · {{ site_name }}{% endif %}</title>
  <link rel="stylesheet" href="{{ root }}assets/style.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{{ root }}index.html">{{ site_name }}</a>
    <span class="tagline">{{ tagline }}</span>
  </header>
  <div class="shell">
    <aside class="sidebar">
      <nav>
        {% for item in nav %}
        <a class="{% if item.href == current %}active{% endif %}" href="{{ root }}{{ item.href }}">{{ item.nav }}</a>
        {% endfor %}
      </nav>
    </aside>
    <main class="content">
      <p class="eyebrow">{{ meta.nav }} / {{ meta.title }}</p>
      <article>{{ content|safe }}</article>
      <nav class="pager">
        {% if prev %}<a href="{{ prev.href }}">← {{ prev.nav }}</a>{% else %}<span></span>{% endif %}
        {% if next %}<a href="{{ next.href }}">{{ next.nav }} →</a>{% else %}<span></span>{% endif %}
      </nav>
    </main>
    <aside class="toc">
      <p class="toc-title">本页目录</p>
      {% for item in page_toc %}
      <a class="level-{{ item.level }}" href="#{{ item.id }}">{{ item.name }}</a>
      {% endfor %}
    </aside>
  </div>
  <footer class="footer">示例文档站 · 生成于本地</footer>
</body>
</html>
"""

CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; background: #f6f5f0; color: #24211c; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; line-height: 1.8; }
.topbar { display: flex; align-items: baseline; gap: 16px; padding: 18px 32px; background: #20342f; color: #f4f1e8; }
.brand { color: #f4f1e8; font-weight: 700; text-decoration: none; letter-spacing: 0.02em; }
.tagline { color: #a9c2b7; font-size: 13px; }
.shell { display: grid; grid-template-columns: 176px minmax(0, 720px) 180px; gap: 28px; max-width: 1180px; margin: 32px auto; padding: 0 24px; }
.sidebar, .toc { position: sticky; top: 24px; align-self: start; }
.sidebar nav { display: flex; flex-direction: column; gap: 4px; }
.sidebar a { padding: 7px 10px; border-radius: 6px; color: #3c4a44; text-decoration: none; font-size: 14px; }
.sidebar a:hover, .sidebar a.active { background: #e8e4d9; color: #1d3a32; }
.content { background: #fff; border: 1px solid #e5e0d4; border-radius: 10px; padding: 32px 40px; min-width: 0; }
.eyebrow { margin: 0 0 4px; color: #7b8b83; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; }
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
.pager { display: flex; justify-content: space-between; gap: 16px; margin-top: 40px; padding-top: 16px; border-top: 1px solid #ece7db; font-size: 14px; }
.toc { display: flex; flex-direction: column; gap: 2px; font-size: 13px; }
.toc-title { margin: 0 0 6px; color: #7b8b83; font-size: 12px; letter-spacing: 0.08em; }
.toc a { padding: 3px 0; color: #55665e; text-decoration: none; }
.toc a:hover { color: #1d3a32; }
.toc .level-3 { padding-left: 12px; }
.footer { max-width: 1180px; margin: 0 auto 32px; padding: 0 24px; color: #8a968f; font-size: 12px; }
@media (max-width: 980px) { .shell { grid-template-columns: 1fr; } .sidebar, .toc { position: static; } .toc { display: none; } }
"""

env = Environment(loader=DictLoader({"base.html": BASE}), autoescape=True)
template = env.get_template("base.html")
print("模板长度:", len(BASE))
print("样式长度:", len(CSS))


if site_dir.exists():
    shutil.rmtree(site_dir)
(site_dir / "assets").mkdir(parents=True, exist_ok=True)
(site_dir / "assets" / "style.css").write_text(CSS, encoding="utf-8")

nav = [{"nav": page["meta"]["nav"], "href": page["output"]} for page in pages]
page_anchors = {}

for position, page in enumerate(pages):
    html, toc_tokens = render_markdown(page["body"])
    page_toc = flatten_toc(toc_tokens)
    html = rewrite_html_links(html)
    root = "../" * page["output"].count("/")
    previous = pages[position - 1] if position > 0 else None
    following = pages[position + 1] if position < len(pages) - 1 else None

    def rel_link(other):
        base = posixpath.dirname(page["output"]) or "."
        return posixpath.relpath(other["output"], start=base)

    rendered = template.render(
        meta=page["meta"],
        site_name="课程文档站",
        tagline="Markdown 与文档工程示例",
        root=root,
        nav=nav,
        current=page["output"],
        content=html,
        page_toc=page_toc,
        prev={"nav": previous["meta"]["nav"], "href": rel_link(previous)} if previous else None,
        next={"nav": following["meta"]["nav"], "href": rel_link(following)} if following else None,
    )

    target = site_dir / page["output"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    page_anchors[page["output"]] = {token["id"] for token in page_toc}
    print(f"{page['output']:24} {len(rendered):>6} 字节  {page['meta']['title']}")

print()
print("页面数量:", len(pages))
print("样式文件:", (site_dir / "assets" / "style.css").stat().st_size, "字节")


link_re = re.compile(r'href="([^"]+)"')
issues = []
checked = 0
for page in pages:
    html = (site_dir / page["output"]).read_text(encoding="utf-8")
    for href in link_re.findall(html):
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        checked += 1
        file_part, _, anchor = href.partition("#")
        target = (site_dir / page["output"]).parent / file_part
        if not target.exists():
            issues.append(f"{page['output']} -> {href} 文件不存在")
            continue
        target_rel = target.resolve().relative_to(site_dir.resolve()).as_posix()
        if anchor and anchor not in page_anchors.get(target_rel, set()):
            issues.append(f"{page['output']} -> {href} 锚点不存在")

all_html = "\n".join(
    (site_dir / page["output"]).read_text(encoding="utf-8") for page in pages
)
external = re.findall(r'(?:href|src)="https?://', all_html)
scripts = re.findall(r"<script", all_html)

entry = site_dir / "index.html"
title = re.search(r"<title>(.*?)</title>", entry.read_text(encoding="utf-8")).group(1)

print("站内 href:", checked, "个")
print("链接问题:", len(issues))
for issue in issues:
    print("-", issue)
print("外部资源:", len(external))
print("脚本标签:", len(scripts))
print()
print("入口文件:", entry)
print("页面标题:", title)
print("入口大小:", entry.stat().st_size, "字节")
print("离线打开：在文件管理器里双击 index.html 即可。")

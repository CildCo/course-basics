import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"没有找到 assets/{name}")

SITE = data_path("site")
OUTPUT = SITE.parent.parent / "output"
OUTPUT.mkdir(exist_ok=True)
print("站点目录：", SITE.name)
print("输出目录：", OUTPUT.name)
print("页面文件：", sorted(path.name for path in SITE.glob("*.html")))

import hashlib
import json
import re
import shutil
import threading
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin, urlsplit, urlunsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup


class CountingHandler(SimpleHTTPRequestHandler):
    hits = 0
    lock = threading.Lock()
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        with self.lock:
            type(self).hits += 1
        super().do_GET()


CountingHandler.hits = 0
server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(CountingHandler, directory=str(SITE))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"

session = requests.Session()
session.headers.update({"User-Agent": "CourseReader/1.0"})
CACHE_DIR = OUTPUT / "cache"
shutil.rmtree(CACHE_DIR, ignore_errors=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
print("本地站点已启动：", BASE.startswith("http://127.0.0.1:"))
print("缓存目录：", CACHE_DIR.name)


def collect_links():
    raw = []
    pages = []
    page = BASE + "/index.html"
    visited = set()
    while page and page not in visited:
        visited.add(page)
        response = session.get(page, timeout=3)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        raw.extend(
            urljoin(page, link["href"])
            for link in soup.select("a[href*='detail/']")
        )
        pages.append(page)
        next_link = soup.select_one('nav.pagination a[rel="next"]')
        page = urljoin(page, next_link["href"]) if next_link else None
    return raw, pages

def canonical(url):
    parts = urlsplit(url)
    path = re.sub(r"/+", "/", parts.path)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))

raw_links, pages = collect_links()
unique_links = []
for url in raw_links:
    key = canonical(url)
    if key not in unique_links:
        unique_links.append(key)

seen = Counter(canonical(url) for url in raw_links)
print("列表页：", [urlsplit(page).path for page in pages])
print("原始详情链接：", len(raw_links))
print("规范化后：", len(unique_links))
print("重复链接：")
for key, count in seen.items():
    if count > 1:
        print(" ", key.split("/")[-1], "出现", count, "次")


def cache_path(url):
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.html"

def fetch_cached(url):
    path = cache_path(url)
    if path.exists():
        return path.read_text(encoding="utf-8"), "缓存"
    response = session.get(url, timeout=3)
    response.raise_for_status()
    text = response.text
    path.write_text(text, encoding="utf-8")
    return text, "网络"

before = CountingHandler.hits
pages_html = {}
first_modes = Counter()
for url in unique_links:
    html, mode = fetch_cached(url)
    pages_html[url] = html
    first_modes[mode] += 1
after_first = CountingHandler.hits

for url in unique_links:
    fetch_cached(url)
after_second = CountingHandler.hits

print("第一次页面来源：", dict(first_modes))
print("第一次真实网络请求：", after_first - before)
print("第二次新增网络请求：", after_second - after_first)
print("第二次命中缓存：", len(unique_links))


records = []
for url in unique_links:
    soup = BeautifulSoup(pages_html[url], "lxml")
    box = soup.select_one("main#course-detail")
    title = box.select_one("h1").get_text(strip=True)
    content = re.sub(r"\s+", "", box.get_text(" ", strip=True))
    records.append(
        {
            "id": box.get("data-course-id"),
            "title": title,
            "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest()[:12],
            "url_path": urlsplit(url).path,
        }
    )

df = pd.DataFrame(records)
print(df.to_string(index=False))
print("记录数：", len(df), "内容哈希唯一值：", df["content_hash"].nunique())
print("是否全部唯一：", df["content_hash"].is_unique)


report = {
    "raw_links": len(raw_links),
    "unique_links": len(unique_links),
    "duplicate_links": len(raw_links) - len(unique_links),
    "first_network_requests": after_first - before,
    "second_network_requests": after_second - after_first,
    "cache_hits": len(unique_links),
    "content_hash_unique": int(df["content_hash"].nunique()),
}
(OUTPUT / "dedupe_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
df.to_csv(OUTPUT / "courses_deduped.csv", index=False, encoding="utf-8-sig")
print("去重报告：", json.dumps(report, ensure_ascii=False))


server.shutdown()
server.server_close()
print("本地站点已关闭")

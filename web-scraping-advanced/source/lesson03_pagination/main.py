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

import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests

class SiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        pass

server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(SiteHandler, directory=str(SITE))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"
print("本地站点已启动：", BASE.startswith("http://127.0.0.1:"))

session = requests.Session()
session.headers.update({"User-Agent": "CourseReader/1.0"})


def fetch(url):
    response = session.get(url, timeout=3)
    response.raise_for_status()
    return response.text

def parse_list(html, current_url):
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for card in soup.select("article.course-card"):
        link = card.select_one("h2.title a")
        if not link:
            continue
        rows.append(
            {
                "id": card.get("data-course-id"),
                "title": link.get_text(strip=True),
                "href": urljoin(current_url, link["href"]),
                "level": card.select_one(".level").get_text(strip=True),
                "price": int(re.sub(r"\D", "", card.select_one(".price").get_text())),
            }
        )
    next_link = soup.select_one('nav.pagination a[rel="next"]')
    next_url = urljoin(current_url, next_link["href"]) if next_link else None
    return rows, next_url

list_rows = []
visited = set()
url = BASE + "/index.html"
page_no = 0
while url and url not in visited:
    visited.add(url)
    page_no += 1
    rows, next_url = parse_list(fetch(url), url)
    print(f"第 {page_no} 页：{len(rows)} 门，有下一页={next_url is not None}")
    list_rows.extend(rows)
    url = next_url

print("列表页共收集：", len(list_rows), "门")
print("详情页地址示例：", list_rows[0]["href"].split("/")[-1])


def text_of(node, default=""):
    return node.get_text(strip=True) if node else default

def parse_detail(html, url):
    soup = BeautifulSoup(html, "lxml")
    box = soup.select_one("main#course-detail")
    price_node = soup.select_one(".price")
    price_text = text_of(price_node)
    price = int(price_node.get("data-price") or re.sub(r"\D", "", price_text))
    return {
        "id": box.get("data-course-id"),
        "title": text_of(soup.select_one("h1.course-title")),
        "instructor": text_of(soup.select_one(".instructor strong")),
        "level": text_of(soup.select_one(".level")).replace("难度：", ""),
        "duration": text_of(soup.select_one(".duration")).replace("时长：", ""),
        "lessons": int(re.sub(r"\D", "", text_of(soup.select_one(".lesson-count")))),
        "price": price,
        "students": int(re.sub(r"\D", "", text_of(soup.select_one(".students")))),
        "updated": text_of(soup.select_one(".updated")).replace("更新：", ""),
        "tags": [tag.get_text(strip=True) for tag in soup.select("ul.tags li")],
        "url": url,
    }

records = []
for row in list_rows:
    detail = parse_detail(fetch(row["href"]), row["href"])
    records.append(detail)

df = pd.DataFrame(records)
print(df[["id", "title", "instructor", "level", "price", "students", "updated"]].to_string(index=False))
print("详情页数量：", len(df), "去重后：", df["id"].nunique())


out = OUTPUT / "courses_page.csv"
df.to_csv(out, index=False, encoding="utf-8-sig")
print("已写入：", out.name)
print("行数：", len(df), "列数：", len(df.columns))
print("价格区间：", int(df["price"].min()), "到", int(df["price"].max()))
print(df.groupby("level")["price"].mean().round(1).to_string())


server.shutdown()
server.server_close()
print("本地站点已关闭")

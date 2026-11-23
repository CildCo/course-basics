import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def find_assets():
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("没有找到 assets 目录")


class SiteHandler(SimpleHTTPRequestHandler):
    # 明确声明 UTF-8，避免浏览器和客户端猜错编码
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        # 练习时不需要每次请求都刷日志
        pass


site_dir = find_assets() / "site"
handler = partial(SiteHandler, directory=str(site_dir))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base_url = f"http://127.0.0.1:{server.server_address[1]}"
print("本地站点已启动：", base_url.startswith("http://127.0.0.1:"))
print("站点目录：", site_dir.name)


import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

all_links = []
for page in ["/index.html", "/page2.html"]:
    page_soup = BeautifulSoup(
        requests.get(base_url + page, timeout=5).text, "html.parser"
    )
    for link in page_soup.select("a[href*='detail/']"):
        all_links.append(urljoin(base_url, link["href"]))
print("抓到的详情链接：", len(all_links))


unique = {}
for url in all_links:
    key = Path(urlparse(url).path).name
    unique.setdefault(key, url)
print("去重前：", len(all_links))
print("去重后：", len(unique))


import re

def parse_price(text):
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def parse_rating(text):
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


for raw in ["￥59.00", "￥ 45.8", "59 元", "48 元"]:
    print(raw, "->", parse_price(raw))


records = []
for key, url in unique.items():
    detail_soup = BeautifulSoup(
        requests.get(url, timeout=5).text, "html.parser"
    )
    meta = {}
    for item in detail_soup.select(".book-meta li"):
        name, _, value = item.get_text(strip=True).partition("：")
        meta[name] = value
    records.append(
        {
            "book_id": key.removeprefix("book-").removesuffix(".html"),
            "title": detail_soup.select_one(".book-title").get_text(strip=True),
            "author": detail_soup.select_one(".book-author")
            .get_text(strip=True)
            .removeprefix("作者："),
            "price": parse_price(
                detail_soup.select_one(".book-price").get_text(strip=True)
            ),
            "rating": parse_rating(
                detail_soup.select_one(".book-rating").get_text(strip=True)
            ),
            "category": meta["分类"],
            "pages": int(meta["页数"].replace(" 页", "")),
            "publisher": meta["出版社"],
            "summary": detail_soup.select_one(".book-summary").get_text(strip=True),
        }
    )
print("清洗后记录：", len(records))
first = records[0]
print(first["title"], "|", first["price"], "|", first["rating"], "|", first["category"])


records.sort(key=lambda row: (-row["rating"], row["price"]))
for rank, row in enumerate(records, 1):
    print(rank, row["title"], row["rating"], row["price"])


import csv

output_dir = Path.cwd() / "output"
output_dir.mkdir(exist_ok=True)
csv_path = output_dir / "books.csv"
columns = [
    "book_id", "title", "author", "price", "rating",
    "category", "pages", "publisher", "summary",
]
with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    writer.writerows(records)
print("已保存：", csv_path.name)
print("数据行数：", len(records))
with csv_path.open(encoding="utf-8") as handle:
    saved_lines = handle.read().splitlines()
print("前 3 行：")
for line in saved_lines[:3]:
    print(line)


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

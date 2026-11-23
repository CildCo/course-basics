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


from urllib.robotparser import RobotFileParser

parser = RobotFileParser()
parser.set_url(base_url + "/robots.txt")
parser.read()
allowed = parser.can_fetch("*", base_url + "/")
print("robots.txt 允许抓取列表页：", allowed)
if not allowed:
    raise RuntimeError("站点规则不允许抓取，停止任务")


import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

links = []
for page in ["/index.html", "/page2.html"]:
    page_soup = BeautifulSoup(
        requests.get(base_url + page, timeout=5).text, "html.parser"
    )
    for link in page_soup.select("a[href*='detail/']"):
        links.append(urljoin(base_url, link["href"]))
unique = {}
for url in links:
    unique.setdefault(Path(urlparse(url).path).name, url)
print("页面入口：", len(links))
print("去重后详情页：", len(unique))


import re

def parse_number(text):
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


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
            "price": parse_number(
                detail_soup.select_one(".book-price").get_text(strip=True)
            ),
            "rating": parse_number(
                detail_soup.select_one(".book-rating").get_text(strip=True)
            ),
            "category": meta["分类"],
            "pages": int(meta["页数"].replace(" 页", "")),
            "publisher": meta["出版社"],
            "summary": detail_soup.select_one(".book-summary").get_text(strip=True),
        }
    )
records.sort(key=lambda row: (-row["rating"], row["price"]))
print("有效记录：", len(records))
print("第一本：", records[0]["title"], records[0]["rating"])


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
for row in records[:3]:
    print(row["title"], "|", row["price"], "|", row["rating"])


from collections import Counter

prices = [row["price"] for row in records]
ratings = [row["rating"] for row in records]
categories = Counter(row["category"] for row in records)
print("书名数量：", len(records))
print("平均价格：", round(sum(prices) / len(prices), 2), "元")
print("最低价格：", min(prices), "元")
print("最高评分：", max(ratings))
print("最低评分：", min(ratings))
print("分类分布：", dict(sorted(categories.items(), key=lambda kv: (-kv[1], kv[0]))))
print("评分前三：")
for row in sorted(records, key=lambda item: (-item["rating"], item["price"]))[:3]:
    print(" ", row["title"], row["rating"])


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

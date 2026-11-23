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
from urllib.parse import urljoin

pages = ["/index.html", "/page2.html"]
detail_urls = []
for page in pages:
    page_html = requests.get(base_url + page, timeout=5).text
    page_soup = BeautifulSoup(page_html, "html.parser")
    links = page_soup.select(".book-card .book-title a")
    print(f"{page}：{len(links)} 本")
    for link in links:
        detail_urls.append(urljoin(base_url, link["href"]))
print("详情链接总数：", len(detail_urls))


def parse_detail(url):
    detail_soup = BeautifulSoup(
        requests.get(url, timeout=5).text, "html.parser"
    )
    meta = {}
    for item in detail_soup.select(".book-meta li"):
        key, _, value = item.get_text(strip=True).partition("：")
        meta[key] = value
    return {
        "title": detail_soup.select_one(".book-title").get_text(strip=True),
        "author": detail_soup.select_one(".book-author")
        .get_text(strip=True)
        .removeprefix("作者："),
        "price": detail_soup.select_one(".book-price").get_text(strip=True),
        "rating": detail_soup.select_one(".book-rating").get_text(strip=True),
        "summary": detail_soup.select_one(".book-summary").get_text(strip=True),
        "category": meta["分类"],
        "pages": meta["页数"],
        "publisher": meta["出版社"],
    }


books = [parse_detail(url) for url in detail_urls]
print("采集到书籍数：", len(books))
for book in books[:3]:
    print(book["title"], "|", book["author"], "|", book["price"], "|", book["rating"])
print("第二页书名：", [book["title"] for book in books[6:]])


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

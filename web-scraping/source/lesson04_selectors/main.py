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

html = requests.get(base_url + "/index.html", timeout=5).text
soup = BeautifulSoup(html, "html.parser")
cards = soup.select(".book-card")
print("卡片数量：", len(cards))


import json

titles = [card.select_one(".book-title").get_text(strip=True) for card in cards]
print("全部书名：", titles)

rows = []
for card in cards:
    rows.append(
        {
            "title": card.select_one(".book-title").get_text(strip=True),
            "author": card.select_one(".book-author").get_text(strip=True),
            "price": card.select_one(".book-price").get_text(strip=True),
            "rating": card.select_one(".book-rating").get_text(strip=True),
        }
    )
print(json.dumps(rows[:2], ensure_ascii=False, indent=2))


table = soup.select_one("table.rank-table")
headers = [th.get_text(strip=True) for th in table.select("thead th")]
print("表头：", headers)
for row in table.select("tbody tr"):
    cells = [td.get_text(strip=True) for td in row.select("td")]
    print(cells)


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

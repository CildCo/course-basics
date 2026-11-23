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
print("页面标题：", soup.title.get_text(strip=True))
print("链接数量：", len(soup.find_all("a")))
print("书名标题数量：", len(soup.find_all("h3", class_="book-title")))


first_card = soup.find("article", class_="book-card")
print("书名：", first_card.find("h3", class_="book-title").get_text(strip=True))
print("作者：", first_card.find("p", class_="book-author").get_text(strip=True))
print("价格：", first_card.find("p", class_="book-price").get_text(strip=True))
print("评分：", first_card.find("p", class_="book-rating").get_text(strip=True))


for link in soup.find_all("a", href=True)[:8]:
    print(link.get_text(strip=True), "->", link["href"])


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

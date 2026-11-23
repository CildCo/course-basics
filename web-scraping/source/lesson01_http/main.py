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


from urllib.request import urlopen

with urlopen(base_url + "/index.html", timeout=5) as response:
    html = response.read().decode("utf-8")
    print("状态码：", response.status)
    print("Content-Type：", response.headers["Content-Type"])
    print("Content-Length：", response.headers["Content-Length"])
    print("HTML 片段（前 10 行）：")
    print("\n".join(html.splitlines()[:10]))


import http.client

connection = http.client.HTTPConnection(
    "127.0.0.1", server.server_address[1], timeout=5
)
connection.request("GET", "/detail/book-01.html")
response = connection.getresponse()
print("请求行：GET /detail/book-01.html HTTP/1.1")
print("状态：", response.status, response.reason)
print("内容类型：", response.getheader("Content-Type"))
print("内容长度：", response.getheader("Content-Length"))
response.read()
connection.close()


from collections import Counter
import re

body = html.split("<body", 1)[1]
tags = re.findall(r"<([a-z0-9]+)[ >]", body)
print("body 中最常见的 5 种标签：")
for tag, count in Counter(tags).most_common(5):
    print(f"  <{tag}>：{count} 个")


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

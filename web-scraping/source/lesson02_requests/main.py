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

url = base_url + "/index.html"
response = requests.get(
    url,
    timeout=5,
    headers={"User-Agent": "MaidaiCourseBot/1.0"},
)
print("状态码：", response.status_code)
print("编码：", response.encoding)
print("文本长度：", len(response.text))
title = response.text.split("<title>")[1].split("</title>")[0]
print("页面标题：", title)


try:
    missing = requests.get(base_url + "/missing.html", timeout=5)
    missing.raise_for_status()
except requests.HTTPError as exc:
    print("捕获 HTTPError，状态码：", exc.response.status_code)


print("请求头 User-Agent：", response.request.headers["User-Agent"])
print("响应头 Content-Type：", response.headers["Content-Type"])
print("响应头 Content-Length：", response.headers["Content-Length"])


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

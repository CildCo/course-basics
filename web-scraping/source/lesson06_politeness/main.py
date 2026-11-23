import threading
import time
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
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        pass


class PolitenessHandler(SiteHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/slow":
            time.sleep(1.0)
            body = "慢响应示例".encode("utf-8")
            try:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        super().do_GET()


site_dir = find_assets() / "site"
handler = partial(PolitenessHandler, directory=str(site_dir))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base_url = f"http://127.0.0.1:{server.server_address[1]}"
print("本地站点已启动：", base_url.startswith("http://127.0.0.1:"))
print("慢响应接口：/slow")


from urllib.robotparser import RobotFileParser

parser = RobotFileParser()
parser.set_url(base_url + "/robots.txt")
parser.read()
print("允许抓取首页：", parser.can_fetch("*", base_url + "/"))
print("允许抓取后台：", parser.can_fetch("*", base_url + "/admin/"))
print("允许抓取详情页：", parser.can_fetch("*", base_url + "/detail/book-03.html"))


import requests

paths = ["/index.html", "/page2.html", "/detail/book-01.html"]
for index, path in enumerate(paths, 1):
    response = requests.get(base_url + path, timeout=5)
    print(f"第 {index} 次请求 {path} -> {response.status_code}")
    time.sleep(0.2)
print("每次请求之间等待 0.2 秒")


try:
    response = requests.get(base_url + "/missing.html", timeout=5)
    response.raise_for_status()
except requests.HTTPError as exc:
    print("404 处理：", exc.response.status_code, "，记录后跳过")


attempts = 3
for attempt in range(1, attempts + 1):
    try:
        requests.get(base_url + "/slow", timeout=0.2)
    except requests.Timeout:
        print(f"第 {attempt} 次请求超时")
print("重试结束：记录失败，继续下一项")


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地站点已关闭")

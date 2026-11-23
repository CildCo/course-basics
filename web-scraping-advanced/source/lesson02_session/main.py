import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import requests

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

class SessionHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        pass

    def _plain(self, status, text, extra_headers=None):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/session/start":
            self._plain(
                200,
                "会话已创建，后续请求请带上 Cookie",
                {"Set-Cookie": "course_session=abc123; Path=/; HttpOnly"},
            )
            return
        if path == "/session/check":
            cookie = self.headers.get("Cookie", "（没有 Cookie）")
            self._plain(200, f"服务器收到的 Cookie：{cookie}")
            return
        if path == "/slow":
            time.sleep(1.0)
            self._plain(200, "慢响应完成")
            return
        super().do_GET()

server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(SessionHandler, directory=str(SITE))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"
print("本地站点已启动：", BASE.startswith("http://127.0.0.1:"))
print("练习页面存在：", (SITE / "index.html").exists())


session = requests.Session()
session.headers.update(
    {
        "User-Agent": "CourseReader/1.0 (local practice; contact: reader@example.test)",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
)

start = session.get(BASE + "/session/start", timeout=3)
print("第一次状态：", start.status_code)
print("第一次响应：", start.text)
print("CookieJar：", session.cookies.get_dict())

check = session.get(BASE + "/session/check", timeout=3)
print("第二次状态：", check.status_code)
print("第二次响应：", check.text)
print("实际发送的 User-Agent：", check.request.headers["User-Agent"])


normal = session.get(BASE + "/index.html", timeout=(0.5, 2))
print("列表页状态：", normal.status_code)
print("本次设置的超时：连接 0.5 秒，读取 2 秒")
print("实际耗时：", round(normal.elapsed.total_seconds(), 3), "秒")
print("Content-Type：", normal.headers.get("Content-Type"))

try:
    session.get(BASE + "/slow", timeout=0.2)
except requests.Timeout as exc:
    print("捕获超时：", type(exc).__name__)
    print("服务端需要约 1.0 秒，读取超时只给了 0.2 秒")


server.shutdown()
server.server_close()
print("本地站点已关闭")

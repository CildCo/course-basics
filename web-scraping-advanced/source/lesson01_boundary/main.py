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


from urllib.robotparser import RobotFileParser

robots_text = (SITE / "robots.txt").read_text(encoding="utf-8")
print(robots_text.strip())

rules = RobotFileParser()
rules.parse(robots_text.splitlines())

bot = "CourseReader/1.0"
for path in [
    "/index.html",
    "/page2.html",
    "/detail/course-01.html",
    "/admin/export",
    "/detail/draft-01.html",
]:
    print(f"{path:28} 允许={rules.can_fetch(bot, path)}")
print("站点要求的抓取间隔：", rules.crawl_delay(bot), "秒")


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

import time

delay = rules.crawl_delay(bot) or 1.0
headers = {"User-Agent": bot}
paths = ["/index.html", "/page2.html", "/detail/course-01.html"]

started_at = time.monotonic()
last_start = None
rows = []
for path in paths:
    if last_start is not None:
        wait = max(0.0, delay - (time.monotonic() - last_start))
        time.sleep(wait)
    started = time.monotonic()
    response = requests.get(BASE + path, headers=headers, timeout=3)
    last_start = started
    rows.append(
        {
            "path": path,
            "status": response.status_code,
            "bytes": len(response.content),
            "offset": round(started - started_at, 2),
        }
    )

for row in rows:
    print(
        f"{row['path']:24} 状态={row['status']} "
        f"字节={row['bytes']} 起始={row['offset']:.2f}s"
    )
print("两次请求之间至少间隔：", delay, "秒")

server.shutdown()
server.server_close()
print("本地站点已关闭")


checklist = [
    "先读取 robots.txt 和站点条款",
    "使用可识别的 User-Agent",
    "遵守 Crawl-delay 或更慢的节奏",
    "只采集公开页面，不绕过登录和付费墙",
    "遇到 403 或明确拒绝时停止，而不是换 IP 继续",
]
for index, item in enumerate(checklist, 1):
    print(f"{index}. {item}")

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
import random
import re
import threading
import time
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

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

class FlakyHandler(SimpleHTTPRequestHandler):
    counts = {}
    lock = threading.Lock()
    fail_plan = {"/detail/course-06.html": 2, "/detail/course-08.html": 1}
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = urlparse(self.path).path
        with self.lock:
            seen = self.counts.get(path, 0) + 1
            self.counts[path] = seen
        if seen <= self.fail_plan.get(path, 0):
            body = b"temporary unavailable"
            self.send_response(503)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

FlakyHandler.counts = {}
server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(FlakyHandler, directory=str(SITE))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"

session = requests.Session()
session.headers.update({"User-Agent": "CourseReader/1.0"})
CHECKPOINT = OUTPUT / "checkpoint.json"
CHECKPOINT.unlink(missing_ok=True)
RNG = random.Random(20261025)
print("本地站点已启动：", BASE.startswith("http://127.0.0.1:"))
print("故障计划：", FlakyHandler.fail_plan)


def collect_detail_urls():
    urls = []
    page = BASE + "/index.html"
    visited = set()
    while page and page not in visited:
        visited.add(page)
        response = session.get(page, timeout=3)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        for card in soup.select("article.course-card"):
            link = card.select_one("h2.title a")
            if not link:
                continue
            url = urljoin(page, link["href"])
            if url not in urls:
                urls.append(url)
        next_link = soup.select_one('nav.pagination a[rel="next"]')
        page = urljoin(page, next_link["href"]) if next_link else None
    return urls

detail_urls = [
    (Path(urlparse(url).path).stem, url) for url in collect_detail_urls()
]
print("详情页数量：", len(detail_urls))
for course_id, url in detail_urls:
    print(course_id, urlparse(url).path)


def fetch_with_retry(url, max_attempts=4, base_delay=0.12):
    attempts = []
    for attempt in range(1, max_attempts + 1):
        started = time.monotonic()
        try:
            response = session.get(url, timeout=2)
        except requests.RequestException as exc:
            wait = round(base_delay * (2 ** (attempt - 1)) + RNG.uniform(0, 0.03), 3)
            attempts.append(
                {
                    "attempt": attempt,
                    "status": None,
                    "error": type(exc).__name__,
                    "wait": wait,
                    "ok": False,
                    "elapsed": round(time.monotonic() - started, 3),
                }
            )
            if attempt == max_attempts:
                raise
            time.sleep(wait)
            continue

        elapsed = round(time.monotonic() - started, 3)
        if response.status_code < 500:
            response.raise_for_status()
            attempts.append(
                {
                    "attempt": attempt,
                    "status": response.status_code,
                    "wait": 0.0,
                    "ok": True,
                    "elapsed": elapsed,
                }
            )
            return response, attempts

        wait = round(base_delay * (2 ** (attempt - 1)) + RNG.uniform(0, 0.03), 3)
        attempts.append(
            {
                "attempt": attempt,
                "status": response.status_code,
                "wait": wait,
                "ok": False,
                "elapsed": elapsed,
            }
        )
        if attempt == max_attempts:
            response.raise_for_status()
        time.sleep(wait)
    raise RuntimeError("重试循环没有返回结果")

def parse_detail(html, url):
    soup = BeautifulSoup(html, "lxml")
    box = soup.select_one("main#course-detail")
    price_node = soup.select_one(".price")
    return {
        "id": box.get("data-course-id"),
        "title": soup.select_one("h1.course-title").get_text(strip=True),
        "instructor": soup.select_one(".instructor strong").get_text(strip=True),
        "price": int(price_node.get("data-price")),
        "students": int(re.sub(r"\D", "", soup.select_one(".students").get_text())),
        "url": url,
    }


state = {"done": []}
records = []
attempt_log = []

for course_id, url in detail_urls[:3]:
    response, attempts = fetch_with_retry(url)
    for item in attempts:
        attempt_log.append({"course_id": course_id, **item})
    records.append(parse_detail(response.text, url))
    state["done"].append(course_id)
    CHECKPOINT.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{course_id} 完成，尝试 {len(attempts)} 次")

print("第一次运行在 3 门后停止")
print("检查点：", CHECKPOINT.read_text(encoding="utf-8").strip())


state = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
done = set(state["done"])
print("从检查点恢复，已完成：", sorted(done))

for course_id, url in detail_urls:
    if course_id in done:
        continue
    response, attempts = fetch_with_retry(url)
    for item in attempts:
        attempt_log.append({"course_id": course_id, **item})
    records.append(parse_detail(response.text, url))
    state["done"].append(course_id)
    done.add(course_id)
    CHECKPOINT.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{course_id} 完成，尝试 {len(attempts)} 次")

print("全部完成：", len(state["done"]), "门")


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import Image, display

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

attempt_counts = Counter(item["course_id"] for item in attempt_log)
course_ids = [course_id for course_id, _ in detail_urls]
values = [attempt_counts[course_id] for course_id in course_ids]
colors = ["#c9853a" if value > 1 else "#2f7d6d" for value in values]

fig, ax = plt.subplots(figsize=(8, 3.8))
bars = ax.bar(course_ids, values, color=colors)
ax.set_title("每门课程详情页的请求尝试次数")
ax.set_ylabel("尝试次数")
ax.set_ylim(0, max(values) + 1)
for bar, value in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.05,
        str(value),
        ha="center",
        va="bottom",
    )
ax.tick_params(axis="x", rotation=25)
fig.tight_layout()
chart = OUTPUT / "retry_stats.png"
fig.savefig(chart, dpi=130)
plt.close(fig)
print("重试统计图：", chart.name)
display(Image(filename=str(chart)))


df = pd.DataFrame(records)
df.to_csv(OUTPUT / "courses_retry.csv", index=False, encoding="utf-8-sig")
(OUTPUT / "retry_log.json").write_text(
    json.dumps(attempt_log, ensure_ascii=False, indent=2), encoding="utf-8"
)

retried = [course_id for course_id in course_ids if attempt_counts[course_id] > 1]
print("课程数：", len(df))
print("总请求尝试：", len(attempt_log))
print("发生重试的课程：", retried)
print(df[["id", "title", "price", "students"]].to_string(index=False))


server.shutdown()
server.server_close()
print("本地站点已关闭")

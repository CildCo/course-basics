import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import hashlib
import json
import random
import re
import shutil
import sqlite3
import threading
import time
from collections import Counter
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

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

BASE_DB = OUTPUT / "pipeline.db"
CSV_PATH = OUTPUT / "pipeline_courses.csv"
REPORT_PATH = OUTPUT / "pipeline_report.json"
CACHE_DIR = OUTPUT / "pipeline_cache"
shutil.rmtree(CACHE_DIR, ignore_errors=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
BASE_DB.unlink(missing_ok=True)

class PipelineHandler(SimpleHTTPRequestHandler):
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
        path = urlsplit(self.path).path
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

PipelineHandler.counts = {}
server = ThreadingHTTPServer(
    ("127.0.0.1", 0), partial(PipelineHandler, directory=str(SITE))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_address[1]}"
UA = "CourseReader/1.0"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})
RNG = random.Random(20261025)
LAST_REQUEST = [0.0]
print("本地站点已启动：", BASE.startswith("http://127.0.0.1:"))
print("管道输出目录：", OUTPUT.name)


robots = RobotFileParser()
robots.parse((SITE / "robots.txt").read_text(encoding="utf-8").splitlines())
allowed = {}
for path in ["/index.html", "/page2.html", "/detail/course-01.html", "/admin/export"]:
    allowed[path] = robots.can_fetch(UA, path)
DELAY = robots.crawl_delay(UA) or 1.0
TIMEOUT = 2
MAX_ATTEMPTS = 4
print("规则检查：", allowed)
print("请求间隔：", DELAY, "秒")
print("超时：", TIMEOUT, "秒，最多尝试：", MAX_ATTEMPTS, "次")


def canonical(url):
    parts = urlsplit(url)
    path = re.sub(r"/+", "/", parts.path)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))

def cache_path(url):
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.html"

def fetch_cached(url):
    path = cache_path(url)
    if path.exists():
        return path.read_text(encoding="utf-8"), "cache"
    wait = max(0.0, DELAY - (time.monotonic() - LAST_REQUEST[0]))
    if wait:
        time.sleep(wait)
    response = SESSION.get(url, timeout=TIMEOUT)
    LAST_REQUEST[0] = time.monotonic()
    response.raise_for_status()
    text = response.text
    path.write_text(text, encoding="utf-8")
    return text, "network"

def fetch_with_retry(url, label):
    attempts = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            text, mode = fetch_cached(url)
            attempts.append(
                {
                    "label": label,
                    "attempt": attempt,
                    "status": 200 if mode == "network" else "cache",
                    "mode": mode,
                    "ok": True,
                }
            )
            return text, mode, attempts
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            wait = round(0.12 * (2 ** (attempt - 1)) + RNG.uniform(0, 0.03), 3)
            attempts.append(
                {
                    "label": label,
                    "attempt": attempt,
                    "status": status,
                    "mode": "network",
                    "wait": wait,
                    "ok": False,
                }
            )
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(wait)
    raise RuntimeError("重试循环没有返回结果")

def parse_list(html, current_url):
    soup = BeautifulSoup(html, "lxml")
    links = []
    for card in soup.select("article.course-card"):
        link = card.select_one("h2.title a")
        if link:
            links.append(urljoin(current_url, link["href"]))
    next_link = soup.select_one('nav.pagination a[rel="next"]')
    next_url = urljoin(current_url, next_link["href"]) if next_link else None
    return links, next_url

def parse_detail(html, url):
    soup = BeautifulSoup(html, "lxml")
    box = soup.select_one("main#course-detail")
    price_node = soup.select_one(".price")
    return {
        "id": box.get("data-course-id"),
        "title": box.select_one("h1").get_text(strip=True),
        "instructor": box.select_one(".instructor strong").get_text(strip=True),
        "level": box.select_one(".level").get_text(strip=True).replace("难度：", ""),
        "price": int(price_node.get("data-price")),
        "students": int(re.sub(r"\D", "", box.select_one(".students").get_text())),
        "updated": box.select_one(".updated").get_text(strip=True).replace("更新：", ""),
        "url": url,
    }


def crawl(base_url):
    modes = Counter()
    attempts = []
    detail_urls = []
    page = base_url + "/index.html"
    visited = set()
    while page and page not in visited:
        visited.add(page)
        html, mode, page_attempts = fetch_with_retry(page, "list")
        modes[mode] += 1
        attempts.extend(page_attempts)
        links, next_url = parse_list(html, page)
        for link in links:
            key = canonical(link)
            if key not in detail_urls:
                detail_urls.append(key)
        page = next_url

    records = []
    for url in detail_urls:
        html, mode, detail_attempts = fetch_with_retry(url, "detail")
        modes[mode] += 1
        attempts.extend(detail_attempts)
        records.append(parse_detail(html, url))
    return records, modes, attempts

def connect():
    conn = sqlite3.connect(BASE_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                instructor TEXT,
                level TEXT,
                price INTEGER,
                students INTEGER,
                updated TEXT,
                content_hash TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
            """
        )

def record_hash(record):
    keys = ("id", "title", "instructor", "level", "price", "students", "updated")
    payload = json.dumps(
        {key: record[key] for key in keys}, ensure_ascii=False, sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def upsert(records):
    now = datetime.now().isoformat(timespec="seconds")
    stats = Counter()
    with connect() as conn:
        for record in records:
            digest = record_hash(record)
            row = conn.execute(
                "SELECT content_hash FROM courses WHERE id = ?", (record["id"],)
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO courses (
                        id, title, instructor, level, price, students,
                        updated, content_hash, first_seen, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["id"], record["title"], record["instructor"],
                        record["level"], record["price"], record["students"],
                        record["updated"], digest, now, now,
                    ),
                )
                stats["inserted"] += 1
            elif row["content_hash"] != digest:
                conn.execute(
                    """
                    UPDATE courses SET
                        title = ?, instructor = ?, level = ?, price = ?,
                        students = ?, updated = ?, content_hash = ?, last_seen = ?
                    WHERE id = ?
                    """,
                    (
                        record["title"], record["instructor"], record["level"],
                        record["price"], record["students"], record["updated"],
                        digest, now, record["id"],
                    ),
                )
                stats["updated"] += 1
            else:
                conn.execute(
                    "UPDATE courses SET last_seen = ? WHERE id = ?",
                    (now, record["id"]),
                )
                stats["unchanged"] += 1
    return stats

init_db()
print("数据库已初始化：", BASE_DB.name)


records_first, modes_first, attempts_first = crawl(BASE)
stats_first = upsert(records_first)

df_first = pd.DataFrame(records_first)
df_first.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
retries_first = sum(1 for item in attempts_first if item["ok"] is False)

print("第一次运行")
print("页面来源：", dict(modes_first))
print("请求尝试：", len(attempts_first), "其中失败重试：", retries_first)
print(
    "写入结果：新增", stats_first["inserted"],
    "更新", stats_first["updated"],
    "未变化", stats_first["unchanged"],
)
print(df_first[["id", "title", "price", "students"]].to_string(index=False))


records_second, modes_second, attempts_second = crawl(BASE)
stats_second = upsert(records_second)
retries_second = sum(1 for item in attempts_second if item["ok"] is False)

print("第二次运行")
print("页面来源：", dict(modes_second))
print("请求尝试：", len(attempts_second), "其中失败重试：", retries_second)
print(
    "写入结果：新增", stats_second["inserted"],
    "更新", stats_second["updated"],
    "未变化", stats_second["unchanged"],
)


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import Image, display

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

labels = ["网络请求", "缓存命中", "失败重试"]
first_values = [modes_first["network"], modes_first["cache"], retries_first]
second_values = [modes_second["network"], modes_second["cache"], retries_second]
positions = range(len(labels))
width = 0.36

fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.bar([x - width / 2 for x in positions], first_values, width, label="第一次运行", color="#2f7d6d")
ax.bar([x + width / 2 for x in positions], second_values, width, label="第二次运行", color="#c9853a")
ax.set_xticks(list(positions), labels)
ax.set_ylabel("次数")
ax.set_title("采集管道的请求来源与重试")
ax.legend()
for values, offset in ((first_values, -width / 2), (second_values, width / 2)):
    for x, value in zip(positions, values):
        ax.text(x + offset, value + 0.1, str(value), ha="center", va="bottom")
fig.tight_layout()
chart = OUTPUT / "pipeline_stats.png"
fig.savefig(chart, dpi=130)
plt.close(fig)
print("管道统计图：", chart.name)
display(Image(filename=str(chart)))


with connect() as conn:
    total = conn.execute("SELECT COUNT(*) AS n FROM courses").fetchone()["n"]
    nulls = conn.execute(
        """
        SELECT COUNT(*) AS n FROM courses
        WHERE title IS NULL OR price IS NULL OR students IS NULL
        """
    ).fetchone()["n"]
    snapshot = pd.read_sql_query(
        "SELECT id, title, price, students, updated FROM courses ORDER BY id", conn
    )

report = {
    "site": "local-qingning-classroom",
    "first_run": {
        "modes": dict(modes_first),
        "attempts": len(attempts_first),
        "retries": retries_first,
        "stats": dict(stats_first),
    },
    "second_run": {
        "modes": dict(modes_second),
        "attempts": len(attempts_second),
        "retries": retries_second,
        "stats": dict(stats_second),
    },
    "db_rows": total,
    "null_rows": nulls,
    "files": [CSV_PATH.name, BASE_DB.name, REPORT_PATH.name],
}
REPORT_PATH.write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("数据库行数：", total)
print("关键字段为空的行：", nulls)
print("复跑新增/更新：", stats_second["inserted"], "/", stats_second["updated"])
print(snapshot.to_string(index=False))
print("产物：", ", ".join(report["files"]))


server.shutdown()
server.server_close()
print("本地站点已关闭")

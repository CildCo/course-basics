import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import hashlib
import json
import re
import shutil
import sqlite3
import threading
from collections import Counter
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin

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

class SiteHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".txt": "text/plain; charset=utf-8",
    }

    def log_message(self, format, *args):
        pass

def start_server(directory):
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(SiteHandler, directory=str(directory))
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"

server, BASE = start_server(SITE)
print("本地站点已启动：", BASE.startswith("http://127.0.0.1:"))
print("站点目录：", SITE.name)


def crawl(base_url):
    session = requests.Session()
    session.headers.update({"User-Agent": "CourseReader/1.0"})
    detail_urls = []
    page = base_url + "/index.html"
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
            if url not in detail_urls:
                detail_urls.append(url)
        next_link = soup.select_one('nav.pagination a[rel="next"]')
        page = urljoin(page, next_link["href"]) if next_link else None

    records = []
    for url in detail_urls:
        response = session.get(url, timeout=3)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        box = soup.select_one("main#course-detail")
        price_node = soup.select_one(".price")
        records.append(
            {
                "id": box.get("data-course-id"),
                "title": box.select_one("h1").get_text(strip=True),
                "instructor": box.select_one(".instructor strong").get_text(strip=True),
                "level": box.select_one(".level").get_text(strip=True).replace("难度：", ""),
                "price": int(price_node.get("data-price")),
                "students": int(
                    re.sub(r"\D", "", box.select_one(".students").get_text())
                ),
                "updated": box.select_one(".updated").get_text(strip=True).replace("更新：", ""),
                "url": url,
            }
        )
    session.close()
    return records

print("采集函数已定义")


DB = OUTPUT / "courses.db"
DB.unlink(missing_ok=True)

def connect():
    conn = sqlite3.connect(DB)
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
print("数据库：", DB.name)
print("表结构：", [row["name"] for row in connect().execute("PRAGMA table_info(courses)")])


records_first = crawl(BASE)
stats_first = upsert(records_first)
server.shutdown()
server.server_close()

print("第一次采集：", len(records_first), "门")
print(
    "写入结果：新增", stats_first["inserted"],
    "更新", stats_first["updated"],
    "未变化", stats_first["unchanged"],
)
with connect() as conn:
    snapshot = pd.read_sql_query(
        "SELECT id, title, price, students, updated FROM courses ORDER BY id", conn
    )
print(snapshot.to_string(index=False))


V2 = OUTPUT / "site_v2"
shutil.rmtree(V2, ignore_errors=True)
shutil.copytree(SITE, V2)

changes = {
    "course-03.html": [
        ('data-price="249"', 'data-price="219"'),
        ("¥249", "¥219"),
        ("1,042 人学习", "1,180 人学习"),
        ("更新：2026-08-30", "更新：2026-10-20"),
    ],
    "course-06.html": [
        ("510 人学习", "536 人学习"),
    ],
}
for name, pairs in changes.items():
    target = V2 / "detail" / name
    text = target.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise ValueError(f"{name} 没有找到待替换内容：{old}")
        text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")

print("已生成站点副本：", V2.name)
print("模拟变化：course-03 价格和人数，course-06 人数")


server, BASE_V2 = start_server(V2)
records_second = crawl(BASE_V2)
stats_second = upsert(records_second)
server.shutdown()
server.server_close()

print("第二次采集：", len(records_second), "门")
print(
    "写入结果：新增", stats_second["inserted"],
    "更新", stats_second["updated"],
    "未变化", stats_second["unchanged"],
)
with connect() as conn:
    snapshot = pd.read_sql_query(
        "SELECT id, title, price, students, updated, last_seen FROM courses ORDER BY id",
        conn,
    )
print(snapshot.to_string(index=False))


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import Image, display

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

labels = ["新增", "更新", "未变化"]
first_values = [
    stats_first["inserted"], stats_first["updated"], stats_first["unchanged"]
]
second_values = [
    stats_second["inserted"], stats_second["updated"], stats_second["unchanged"]
]
positions = range(len(labels))
width = 0.36

fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.bar([x - width / 2 for x in positions], first_values, width, label="第一次运行", color="#2f7d6d")
ax.bar([x + width / 2 for x in positions], second_values, width, label="第二次运行", color="#c9853a")
ax.set_xticks(list(positions), labels)
ax.set_ylabel("记录数")
ax.set_title("两次采集的增量结果")
ax.legend()
for values, offset in ((first_values, -width / 2), (second_values, width / 2)):
    for x, value in zip(positions, values):
        ax.text(x + offset, value + 0.08, str(value), ha="center", va="bottom")
fig.tight_layout()
chart = OUTPUT / "incremental_stats.png"
fig.savefig(chart, dpi=130)
plt.close(fig)
print("增量统计图：", chart.name)
display(Image(filename=str(chart)))


with connect() as conn:
    total = conn.execute("SELECT COUNT(*) AS n FROM courses").fetchone()["n"]
    changed = conn.execute(
        "SELECT id, price, students, updated FROM courses WHERE id IN (?, ?) ORDER BY id",
        ("course-03", "course-06"),
    ).fetchall()

report = {
    "first_run": dict(stats_first),
    "second_run": dict(stats_second),
    "db_rows": total,
    "changed_rows": [dict(row) for row in changed],
}
(OUTPUT / "incremental_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("数据库总行数：", total)
print("变化记录：")
for row in changed:
    print(dict(row))
print("增量报告：", (OUTPUT / "incremental_report.json").name)

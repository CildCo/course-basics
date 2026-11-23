import json
import sqlite3
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


articles = json.loads(data_path("articles.json").read_text(encoding="utf-8"))

conn = sqlite3.connect(":memory:")
conn.execute(
    """
    CREATE TABLE docs (
        id INTEGER PRIMARY KEY,
        payload TEXT NOT NULL CHECK (json_valid(payload)),
        title TEXT GENERATED ALWAYS AS (json_extract(payload, '$.title')) VIRTUAL,
        category TEXT GENERATED ALWAYS AS (json_extract(payload, '$.category')) VIRTUAL,
        tag_count INTEGER GENERATED ALWAYS AS (json_array_length(json_extract(payload, '$.tags'))) STORED
    )
    """
)

with conn:
    conn.executemany(
        "INSERT INTO docs(id, payload) VALUES (?, ?)",
        [
            (
                article["id"],
                json.dumps(
                    {
                        "title": article["title"],
                        "category": article["category"],
                        "tags": article["tags"],
                        "body": article["body"],
                    },
                    ensure_ascii=False,
                ),
            )
            for article in articles
        ],
    )

print("文章数：", conn.execute("SELECT COUNT(*) FROM docs").fetchone()[0])
print()
print("生成列结果：")
for row in conn.execute(
    "SELECT id, title, category, tag_count FROM docs ORDER BY id LIMIT 4"
):
    print(row)


print("json_type 与数组第一个元素：")
for row in conn.execute(
    "SELECT id, json_type(payload, '$.tags'), json_extract(payload, '$.tags[0]') FROM docs ORDER BY id LIMIT 3"
):
    print(row)

print()
print("包含“索引”标签的文章：")
for row in conn.execute(
    """
    SELECT d.id, d.title, j.value
    FROM docs AS d, json_each(d.payload, '$.tags') AS j
    WHERE j.value = '索引'
    ORDER BY d.id
    """
):
    print(row)

print()
print("标签使用次数：")
for row in conn.execute(
    """
    SELECT j.value, COUNT(*) AS uses
    FROM docs AS d, json_each(d.payload, '$.tags') AS j
    GROUP BY j.value
    ORDER BY uses DESC, j.value
    LIMIT 8
    """
):
    print(row)

try:
    conn.execute("INSERT INTO docs(id, payload) VALUES (99, 'not json')")
    print("坏 JSON 写入成功（不应发生）")
except sqlite3.Error as error:
    conn.rollback()
    print()
    print("坏 JSON 被拒绝：", error)


conn.execute("CREATE INDEX idx_docs_title ON docs(title)")

print("按生成列查询的计划：")
for row in conn.execute(
    "EXPLAIN QUERY PLAN SELECT id, title FROM docs WHERE title = ?",
    ("索引原理：从 B 树到查询计划",),
):
    print("  ", row[3])

print()
print("查询结果：", conn.execute(
    "SELECT id, title FROM docs WHERE title = ?",
    ("索引原理：从 B 树到查询计划",),
).fetchall())

conn.execute(
    "UPDATE docs SET payload = json_set(payload, '$.title', '索引原理（修订）') WHERE id = 1"
)
print("更新 payload 后，生成列自动变化：", conn.execute("SELECT id, title FROM docs WHERE id = 1").fetchone())
print("索引列表：", conn.execute("PRAGMA index_list(docs)").fetchall())

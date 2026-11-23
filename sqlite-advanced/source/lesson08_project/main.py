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


notes = json.loads(data_path("knowledge/notes.json").read_text(encoding="utf-8"))
faq = data_path("knowledge/faq.md").read_text(encoding="utf-8")

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
db_path = out / "knowledge.db"
for suffix in ("", "-wal", "-shm"):
    candidate = Path(str(db_path) + suffix)
    if candidate.exists():
        candidate.unlink()

conn = sqlite3.connect(db_path)
print("日志模式：", conn.execute("PRAGMA journal_mode=WAL").fetchone()[0])
conn.execute("PRAGMA foreign_keys=ON")
conn.executescript(
    """
    CREATE TABLE notes (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        tags TEXT NOT NULL CHECK (json_valid(tags)),
        body TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        tag_count INTEGER GENERATED ALWAYS AS (json_array_length(tags)) STORED,
        title_key TEXT GENERATED ALWAYS AS (lower(title)) VIRTUAL
    ) STRICT;

    CREATE INDEX idx_notes_category_updated ON notes(category, updated_at DESC);
    CREATE INDEX idx_notes_title_key ON notes(title_key);

    CREATE VIRTUAL TABLE notes_fts USING fts5(title, body, tokenize='trigram');

    CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN
        INSERT INTO notes_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
    END;
    CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN
        DELETE FROM notes_fts WHERE rowid = old.id;
        INSERT INTO notes_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
    END;
    CREATE TRIGGER notes_ad AFTER DELETE ON notes BEGIN
        DELETE FROM notes_fts WHERE rowid = old.id;
    END;

    PRAGMA user_version=1;
    """
)

with conn:
    conn.executemany(
        "INSERT INTO notes(id, title, category, tags, body, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                note["id"],
                note["title"],
                note["category"],
                json.dumps(note["tags"], ensure_ascii=False),
                note["content"],
                note["updated_at"],
            )
            for note in notes
        ],
    )
    conn.execute(
        "INSERT INTO notes(id, title, category, tags, body, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            max(note["id"] for note in notes) + 1,
            "知识库使用说明",
            "工程实践",
            json.dumps(["知识库", "faq"], ensure_ascii=False),
            faq,
            "2026-10-25",
        ),
    )

print("笔记数：", conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0])
print("分类数：", conn.execute("SELECT COUNT(DISTINCT category) FROM notes").fetchone()[0])
print("user_version：", conn.execute("PRAGMA user_version").fetchone()[0])
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
print("数据库大小：", db_path.stat().st_size, "字节")


term = "索引优化"
search_rows = conn.execute(
    """
    SELECT n.id, n.title, round(notes_fts.rank, 4),
           snippet(notes_fts, 1, '[', ']', '...', 12)
    FROM notes_fts
    JOIN notes AS n ON n.id = notes_fts.rowid
    WHERE notes_fts MATCH ?
    ORDER BY notes_fts.rank
    LIMIT 3
    """,
    (term,),
).fetchall()

print("全文检索", term, "：")
for row in search_rows:
    print(row)

print()
print("分类列表的查询计划：")
for row in conn.execute(
    "EXPLAIN QUERY PLAN SELECT id, title, updated_at FROM notes WHERE category = ? ORDER BY updated_at DESC LIMIT 5",
    ("索引",),
):
    print("  ", row[3])

print()
print("索引分类下最近的笔记：")
for row in conn.execute(
    "SELECT id, title, updated_at FROM notes WHERE category = ? ORDER BY updated_at DESC LIMIT 5",
    ("索引",),
):
    print(row)

print()
print("标签使用次数：")
for row in conn.execute(
    """
    SELECT j.value, COUNT(*) AS uses
    FROM notes AS n, json_each(n.tags) AS j
    GROUP BY j.value
    ORDER BY uses DESC, j.value
    LIMIT 8
    """
):
    print(row)


backup_path = out / "knowledge-backup.db"
for suffix in ("", "-wal", "-shm"):
    candidate = Path(str(backup_path) + suffix)
    if candidate.exists():
        candidate.unlink()

target = sqlite3.connect(backup_path)
conn.backup(target)
target.close()

check = sqlite3.connect(backup_path)
print("备份完整性：", check.execute("PRAGMA integrity_check").fetchone()[0])
print("备份笔记数：", check.execute("SELECT COUNT(*) FROM notes").fetchone()[0])
print("备份大小：", backup_path.stat().st_size, "字节")
check.close()

before = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
try:
    with conn:
        conn.execute(
            "INSERT INTO notes(id, title, category, tags, body, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (999, "坏标签", "测试", "not json", "内容", "2026-10-25"),
        )
        raise RuntimeError("模拟后续步骤失败")
except (sqlite3.Error, RuntimeError) as error:
    print("事务已回滚：", error)

after = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
print("回滚前后行数：", before, "->", after)
print("外键检查：", conn.execute("PRAGMA foreign_key_check").fetchall())


category_rows = conn.execute(
    "SELECT category, COUNT(*) FROM notes GROUP BY category ORDER BY COUNT(*) DESC, category"
).fetchall()
tag_rows = conn.execute(
    """
    SELECT j.value, COUNT(*) AS uses
    FROM notes AS n, json_each(n.tags) AS j
    GROUP BY j.value
    ORDER BY uses DESC, j.value
    LIMIT 5
    """
).fetchall()

report = {
    "generated_at": "2026-10-25",
    "database": db_path.name,
    "notes": conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
    "categories": {name: count for name, count in category_rows},
    "top_tags": [{"tag": tag, "uses": uses} for tag, uses in tag_rows],
    "search": {
        "query": term,
        "matches": [{"id": row[0], "title": row[1]} for row in search_rows],
    },
    "integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    "user_version": conn.execute("PRAGMA user_version").fetchone()[0],
    "backup": backup_path.name,
}

report_path = out / "knowledge-report.json"
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
print()
print("报告文件：", report_path.name)
conn.close()

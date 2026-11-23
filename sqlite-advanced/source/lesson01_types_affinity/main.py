import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute(
    """
    CREATE TABLE readings (
        id INTEGER PRIMARY KEY,
        metric TEXT NOT NULL,
        value NUMERIC,
        note TEXT DEFAULT '',
        recorded_at TEXT NOT NULL,
        UNIQUE (metric, recorded_at),
        CHECK (length(metric) BETWEEN 1 AND 20)
    )
    """
)

rows = [
    ("temperature", "23.5", "字符串形式的小数"),
    ("humidity", 61, "整数"),
    ("pressure", "1013.2", ""),
    ("wind", "light", "无法转成数字"),
]
with conn:
    conn.executemany(
        "INSERT INTO readings(metric, value, note, recorded_at) VALUES (?, ?, ?, ?)",
        [(metric, value, note, "2026-10-25") for metric, value, note in rows],
    )

print("写入后的值与实际类型：")
for row in conn.execute("SELECT metric, value, typeof(value) FROM readings"):
    print(row)

print()
print("表结构：")
for column in conn.execute("PRAGMA table_info(readings)"):
    print(column)


attempts = [
    ("temperature", "30", "2026-10-25", "重复的 metric + recorded_at"),
    (None, "1", "2026-10-26", "metric 为空"),
    ("x" * 21, "1", "2026-10-26", "metric 超过 20 个字符"),
]

for metric, value, recorded_at, label in attempts:
    try:
        conn.execute(
            "INSERT INTO readings(metric, value, recorded_at) VALUES (?, ?, ?)",
            (metric, value, recorded_at),
        )
        conn.commit()
        print(label, "-> 写入成功")
    except sqlite3.IntegrityError as error:
        conn.rollback()
        print(label, "->", error)

print()
print("当前行数：", conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0])


strict = sqlite3.connect(":memory:")
strict.execute(
    """
    CREATE TABLE strict_readings (
        id INTEGER PRIMARY KEY,
        value INTEGER NOT NULL,
        note TEXT
    ) STRICT
    """
)

for value in (42, "42", "abc", 42.0):
    try:
        strict.execute(
            "INSERT INTO strict_readings(value, note) VALUES (?, ?)", (value, "ok")
        )
        row = strict.execute(
            "SELECT value, typeof(value) FROM strict_readings ORDER BY id DESC LIMIT 1"
        ).fetchone()
        print(repr(value), "->", row)
    except sqlite3.IntegrityError as error:
        print(repr(value), "->", error)

import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute(
    """
    CREATE TABLE events (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        payload TEXT NOT NULL
    )
    """
)

rows = []
for i in range(1, 8001):
    rows.append(
        (
            i % 100,
            ("click", "view", "buy")[i % 3],
            f"2026-10-{i % 28 + 1:02d}",
            "payload-" + "x" * 20,
        )
    )
with conn:
    conn.executemany(
        "INSERT INTO events(user_id, event_type, created_at, payload) VALUES (?, ?, ?, ?)",
        rows,
    )

conn.execute(
    "CREATE INDEX idx_events_user_type_time ON events(user_id, event_type, created_at)"
)


def show_plan(label, sql, params=()):
    print(label)
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params):
        print("  ", row[3])
    print()


queries = [
    ("只按 user_id", "SELECT id, payload FROM events WHERE user_id = ?", (7,)),
    (
        "user_id + event_type",
        "SELECT id, payload FROM events WHERE user_id = ? AND event_type = ?",
        (7, "click"),
    ),
    (
        "只按 event_type",
        "SELECT id, payload FROM events WHERE event_type = ?",
        ("click",),
    ),
]

for label, sql, params in queries:
    show_plan(label + "：", sql, params)


print("覆盖查询：只取索引里已有的列")
show_plan(
    "覆盖查询：",
    "SELECT user_id, event_type, created_at FROM events WHERE user_id = ? AND event_type = ?",
    (7, "click"),
)

print("回表查询：还需要 payload")
show_plan(
    "回表查询：",
    "SELECT user_id, event_type, created_at, payload FROM events WHERE user_id = ? AND event_type = ?",
    (7, "click"),
)

print("索引列顺序：")
for row in conn.execute("PRAGMA index_info(idx_events_user_type_time)"):
    print(row)


conn.execute("CREATE INDEX idx_events_type_user ON events(event_type, user_id)")
show_plan(
    "为 event_type 单独建索引后：",
    "SELECT id, payload FROM events WHERE event_type = ?",
    ("click",),
)
print("当前索引：", conn.execute("PRAGMA index_list(events)").fetchall())

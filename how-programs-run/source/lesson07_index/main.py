import sqlite3

connection = sqlite3.connect(":memory:")
connection.execute(
    "CREATE TABLE events (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, amount INTEGER NOT NULL)"
)
rows = (
    (("click" if index % 5 == 0 else "view"), index % 100)
    for index in range(5000)
)
connection.executemany("INSERT INTO events (kind, amount) VALUES (?, ?)", rows)
connection.commit()

print("事件总数：", connection.execute("SELECT count(*) FROM events").fetchone()[0])
print(
    "click 数量：",
    connection.execute("SELECT count(*) FROM events WHERE kind = 'click'").fetchone()[0],
)


query = "SELECT * FROM events WHERE kind = 'click'"
before = connection.execute("EXPLAIN QUERY PLAN " + query).fetchall()

print("加索引前的计划：")
for row in before:
    print(" ", row[3])


connection.execute("CREATE INDEX idx_events_kind ON events(kind)")
after = connection.execute("EXPLAIN QUERY PLAN " + query).fetchall()

print("加索引后的计划：")
for row in after:
    print(" ", row[3])
print()
print("索引列表：", connection.execute("PRAGMA index_list(events)").fetchall())
print("查询结果行数：", len(connection.execute(query).fetchall()))

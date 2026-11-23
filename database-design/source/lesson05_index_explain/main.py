import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute(
    """
    CREATE TABLE orders (
        order_id    INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        status      TEXT NOT NULL,
        created_at  TEXT NOT NULL,
        amount      REAL NOT NULL
    )
    """
)

rows = []
for i in range(1, 3001):
    status = "paid" if i % 4 else "refunded"
    rows.append((i, i % 120, status, f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}", (i % 9 + 1) * 10.0))
conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", rows)


def show_plan(label, sql):
    print(label)
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql):
        print("  ", row[3])
    print()


query = "SELECT order_id, amount FROM orders WHERE customer_id = 42 AND status = 'paid'"
print("订单行数：", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("命中行数：", len(conn.execute(query).fetchall()))
print()
show_plan("建索引前：", query)


show_plan("先建单列索引：", query)
conn.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
show_plan("单列索引后：", query)

print("索引列表：", conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'orders' ORDER BY name"
).fetchall())

conn.execute("DROP INDEX idx_orders_customer")
conn.execute("CREATE INDEX idx_orders_customer_status ON orders(customer_id, status)")
show_plan("复合索引后：", query)


show_plan("只按 status：", "SELECT order_id FROM orders WHERE status = 'paid'")
show_plan("只按 customer_id：", "SELECT order_id FROM orders WHERE customer_id = 42")
show_plan("两列都用：", query)
show_plan("只查索引列：", "SELECT customer_id, status FROM orders WHERE customer_id = 42 AND status = 'paid'")

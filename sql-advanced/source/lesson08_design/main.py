import csv
import sqlite3
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)
db_path = out_dir / "shop_v2.db"
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript("""
CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL UNIQUE,
    region        TEXT NOT NULL,
    level         TEXT NOT NULL CHECK (level IN ('普通', '银卡', '金卡', '钻石')),
    joined_at     TEXT NOT NULL
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date  TEXT NOT NULL,
    category    TEXT NOT NULL,
    product     TEXT NOT NULL,
    units       INTEGER NOT NULL CHECK (units > 0),
    unit_price  REAL NOT NULL CHECK (unit_price >= 0),
    status      TEXT NOT NULL CHECK (status IN ('completed', 'pending', 'cancelled', 'refunded'))
);

CREATE INDEX idx_orders_customer_date ON orders(customer_id, order_date);
""")
print("表结构已创建")


with data_path("customers.csv").open(encoding="utf-8", newline="") as f:
    conn.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
        [(int(r["customer_id"]), r["customer_name"], r["region"], r["level"], r["joined_at"]) for r in csv.DictReader(f)],
    )
with data_path("orders.csv").open(encoding="utf-8", newline="") as f:
    conn.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (int(r["order_id"]), int(r["customer_id"]), r["order_date"], r["category"],
             r["product"], int(r["units"]), float(r["unit_price"]), r["status"])
            for r in csv.DictReader(f)
        ],
    )
conn.commit()

for row in conn.execute("SELECT (SELECT COUNT(*) FROM customers), (SELECT COUNT(*) FROM orders)"):
    print("客户数 / 订单数:", row[0], "/", row[1])


conn.executescript("""
ALTER TABLE customers ADD COLUMN channel TEXT NOT NULL DEFAULT '线下';

UPDATE customers
SET channel = CASE
    WHEN region = '华东' THEN '直营'
    WHEN region = '华南' THEN '经销'
    ELSE '线上'
END;

CREATE TABLE order_events (
    event_id   INTEGER PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    event      TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

for row in conn.execute("PRAGMA table_info(customers)"):
    print(row[1], row[2], "NOT NULL" if row[3] else "", row[4])

print()
for row in conn.execute("SELECT channel, COUNT(*) FROM customers GROUP BY channel ORDER BY channel"):
    print(row[0], row[1])


print("外键检查（应为空）:")
rows = conn.execute("PRAGMA foreign_key_check").fetchall()
print(rows if rows else "无问题")

try:
    conn.execute(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (9999, 999, "2026-11-11", "办公", "笔记本", 1, 39.9, "completed"),
    )
except sqlite3.IntegrityError as exc:
    print("外键拦截:", exc)

try:
    conn.execute("UPDATE customers SET level = '黑卡' WHERE customer_id = 1")
except sqlite3.IntegrityError as exc:
    print("CHECK 拦截:", exc)

print("迁移后客户数:", conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0])
print("迁移后订单数:", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])

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


SCHEMA = """
CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    region        TEXT NOT NULL,
    level         TEXT NOT NULL,
    joined_at     TEXT NOT NULL
);
CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  TEXT NOT NULL,
    category    TEXT NOT NULL,
    product     TEXT NOT NULL,
    units       INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    status      TEXT NOT NULL
);
"""

out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)
db_path = out_dir / "shop.db"
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(db_path)
conn.executescript(SCHEMA)
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
print("数据库文件:", db_path.name, "订单数:", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])


before = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

conn.execute("BEGIN")
conn.execute(
    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    (9001, 1, "2026-11-01", "办公", "笔记本", 3, 39.9, "pending"),
)
during = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
conn.rollback()
after = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

print("事务前:", before)
print("事务中:", during)
print("回滚后:", after)


try:
    conn.execute("BEGIN")
    conn.execute(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (1001, 2, "2026-11-02", "办公", "笔记本", 1, 39.9, "completed"),
    )
    conn.commit()
except sqlite3.IntegrityError as exc:
    conn.rollback()
    print("写入失败:", exc)

print("订单数仍为:", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])


A = sqlite3.connect(db_path)
B = sqlite3.connect(db_path)

A.execute("BEGIN IMMEDIATE")
A.execute(
    "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    (9002, 3, "2026-11-03", "数码", "耳机", 2, 129.0, "completed"),
)

print("A 未提交时，B 看到:", B.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
A.commit()
print("A 提交后，B 看到:", B.execute("SELECT COUNT(*) FROM orders").fetchone()[0])

A.close()
B.close()


A = sqlite3.connect(db_path)
B = sqlite3.connect(db_path, timeout=0)

A.execute("BEGIN IMMEDIATE")
try:
    B.execute("BEGIN IMMEDIATE")
    print("B 拿到了写锁（不应出现）")
except sqlite3.OperationalError as exc:
    print("B 等锁失败:", exc)

A.rollback()
A.close()
B.close()
print("写锁已释放")

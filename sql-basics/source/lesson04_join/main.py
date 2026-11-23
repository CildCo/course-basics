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

def load_sales():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE sales (date TEXT, region TEXT, category TEXT, product TEXT, units INTEGER, price REAL)")
    with data_path("sales.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    conn.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)",
        [(row["date"], row["region"], row["category"], row["product"], int(row["units"]), float(row["price"])) for row in rows],
    )
    return conn

def show(conn, sql):
    cursor = conn.execute(sql)
    print([column[0] for column in cursor.description])
    for row in cursor.fetchall():
        print(row)


conn = load_sales()
conn.execute("CREATE TABLE targets (category TEXT PRIMARY KEY, target REAL)")
conn.executemany("INSERT INTO targets VALUES (?, ?)", [("办公", 2000), ("数码", 1500), ("家居", 800)])
show(conn, "SELECT * FROM targets")


show(conn, """
SELECT s.category, ROUND(SUM(s.units * s.price), 2) AS amount, t.target
FROM sales s
JOIN targets t ON s.category = t.category
GROUP BY s.category, t.target
ORDER BY amount DESC
""")


conn.execute("INSERT INTO targets VALUES ('食品', 500)")
show(conn, """
SELECT t.category, t.target, COUNT(s.product) AS orders
FROM targets t
LEFT JOIN sales s ON s.category = t.category
GROUP BY t.category, t.target
ORDER BY orders DESC
""")

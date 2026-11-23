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
show(conn, "SELECT date, product, units FROM sales LIMIT 5")


show(conn, "SELECT product, units, price FROM sales WHERE category = '办公' LIMIT 5")


show(conn, "SELECT product, units, price FROM sales WHERE units >= 10 AND price < 50")


show(conn, "SELECT product, units FROM sales ORDER BY units DESC LIMIT 5")

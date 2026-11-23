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
show(conn, """
SELECT category, amount
FROM (
    SELECT category, ROUND(SUM(units * price), 2) AS amount
    FROM sales
    GROUP BY category
)
WHERE amount > 3000
ORDER BY amount DESC
""")


show(conn, """
WITH category_amount AS (
    SELECT category, ROUND(SUM(units * price), 2) AS amount
    FROM sales
    GROUP BY category
)
SELECT category, amount
FROM category_amount
WHERE amount > 3000
ORDER BY amount DESC
""")


show(conn, """
WITH monthly AS (
    SELECT substr(date, 1, 7) AS month, ROUND(SUM(units * price), 2) AS amount
    FROM sales
    GROUP BY month
),
ranked AS (
    SELECT month, amount, RANK() OVER (ORDER BY amount DESC) AS rank
    FROM monthly
)
SELECT * FROM ranked ORDER BY rank
""")

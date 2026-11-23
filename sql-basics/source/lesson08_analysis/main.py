import matplotlib
matplotlib.use("Agg")

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


import pandas as pd
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt

conn = load_sales()
category = pd.read_sql_query("""
SELECT category, ROUND(SUM(units * price), 2) AS amount
FROM sales
GROUP BY category
ORDER BY amount DESC
""", conn)
category


fig, ax = plt.subplots(figsize=(6, 3.5))
ax.bar(category["category"], category["amount"], color="#4f7cff")
ax.set_title("分类销售额（SQL 查询）")
ax.set_ylabel("销售额")
plt.tight_layout()


monthly = pd.read_sql_query("""
SELECT substr(date, 1, 7) AS month, ROUND(SUM(units * price), 2) AS amount
FROM sales
GROUP BY month
ORDER BY month
""", conn)
fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(monthly["month"], monthly["amount"], marker="o", color="#2f8f5b")
ax.set_title("月度销售额（SQL 查询）")
ax.set_ylabel("销售额")
plt.xticks(rotation=30)
plt.tight_layout()

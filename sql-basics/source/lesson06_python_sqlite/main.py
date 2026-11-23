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


from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
db_path = output / "sales.db"
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(db_path)
conn.execute("CREATE TABLE sales (date TEXT, region TEXT, category TEXT, product TEXT, units INTEGER, price REAL)")
with data_path("sales.csv").open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))
conn.executemany(
    "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)",
    [(row["date"], row["region"], row["category"], row["product"], int(row["units"]), float(row["price"])) for row in rows],
)
conn.commit()
print("写入行数：", conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0])


cursor = conn.execute("SELECT category, SUM(units) FROM sales GROUP BY category ORDER BY category")
for row in cursor.fetchall():
    print(row)


category = "办公"
cursor = conn.execute("SELECT product, units FROM sales WHERE category = ?", (category,))
print(cursor.fetchall()[:3])

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


conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT, done INTEGER)")
conn.executemany("INSERT INTO notes (title, done) VALUES (?, ?)", [("学 SQL", 0), ("写练习", 0)])
conn.commit()
show(conn, "SELECT * FROM notes")


conn.execute("UPDATE notes SET done = 1 WHERE title = ?", ("学 SQL",))
conn.execute("DELETE FROM notes WHERE title = ?", ("写练习",))
conn.commit()
show(conn, "SELECT * FROM notes")


try:
    with conn:
        conn.execute("INSERT INTO notes (title, done) VALUES (?, ?)", ("事务 A", 0))
        conn.execute("INSERT INTO notes (title, done) VALUES (?, ?)", ("事务 B", 0))
    print("事务提交")
except sqlite3.Error as error:
    print("回滚：", error)
show(conn, "SELECT * FROM notes")

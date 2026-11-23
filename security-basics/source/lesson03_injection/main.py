import re
import sqlite3

connection = sqlite3.connect(":memory:")
connection.executescript(
    """
    CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT);
    INSERT INTO users (username, role) VALUES
        ('alice', 'admin'),
        ('bob', 'editor'),
        ('carol', 'viewer');
    """
)

for row in connection.execute("SELECT id, username, role FROM users"):
    print(row)


username = "' OR '1'='1"
query = f"SELECT id, username, role FROM users WHERE username = '{username}'"
print("拼接后的 SQL:")
print(query)

rows = connection.execute(query).fetchall()
print("返回行数:", len(rows))
for row in rows:
    print(row)


query = "SELECT id, username, role FROM users WHERE username = ?"
rows = connection.execute(query, (username,)).fetchall()
print("参数化后返回行数:", len(rows))
print("用合法用户名查询:")
print(connection.execute(query, ("alice",)).fetchall())


USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")


def find_user(username):
    if not USERNAME_RE.fullmatch(username):
        return "输入不合法"
    return connection.execute(
        "SELECT id, username, role FROM users WHERE username = ?",
        (username,),
    ).fetchall()


print(find_user("alice"))
print(find_user("' OR '1'='1"))
print(find_user("a"))

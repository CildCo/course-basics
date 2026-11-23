import sqlite3

conn = sqlite3.connect(":memory:", isolation_level=None)
conn.executescript(
    """
    CREATE TABLE accounts (
        account_id INTEGER PRIMARY KEY,
        owner      TEXT NOT NULL,
        balance    REAL NOT NULL CHECK (balance >= 0)
    );
    INSERT INTO accounts VALUES (1, '林晓', 500), (2, '陈默', 100);
    """
)


def transfer(from_id, to_id, amount):
    try:
        conn.execute("BEGIN")
        balance = conn.execute(
            "SELECT balance FROM accounts WHERE account_id = ?", (from_id,)
        ).fetchone()[0]
        if balance < amount:
            raise ValueError("余额不足")
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_id = ?",
            (amount, from_id),
        )
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE account_id = ?",
            (amount, to_id),
        )
        conn.execute("COMMIT")
        print(f"转账 {amount} 成功")
    except Exception as error:
        conn.execute("ROLLBACK")
        print(f"转账 {amount} 失败，已回滚：{error}")


transfer(1, 2, 100)
transfer(1, 2, 10000)
print("最终余额：", conn.execute(
    "SELECT account_id, balance FROM accounts ORDER BY account_id"
).fetchall())


import sqlite3
from pathlib import Path


def output_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        if (base / "assets").is_dir():
            folder = base / "output"
            folder.mkdir(exist_ok=True)
            return folder / name
    raise FileNotFoundError("assets")


db_path = output_path("isolation.db")
for suffix in ("", "-wal", "-shm"):
    Path(str(db_path) + suffix).unlink(missing_ok=True)

writer = sqlite3.connect(db_path, isolation_level=None, timeout=5)
writer.execute("PRAGMA journal_mode = WAL")
writer.executescript(
    """
    CREATE TABLE accounts (
        account_id INTEGER PRIMARY KEY,
        balance    REAL NOT NULL
    );
    CREATE TABLE audit_log (
        log_id  INTEGER PRIMARY KEY,
        message TEXT NOT NULL
    );
    INSERT INTO accounts VALUES (1, 100), (2, 100);
    INSERT INTO audit_log VALUES (1, '初始化');
    """
)
reader = sqlite3.connect(db_path, isolation_level=None, timeout=5)

writer.execute("BEGIN")
writer.execute("UPDATE accounts SET balance = 200 WHERE account_id = 1")
print("写入未提交时，另一个连接读到：", reader.execute(
    "SELECT balance FROM accounts WHERE account_id = 1"
).fetchone()[0], "（没有脏读）")
writer.execute("COMMIT")
print("提交后，另一个连接读到：", reader.execute(
    "SELECT balance FROM accounts WHERE account_id = 1"
).fetchone()[0])

reader.execute("BEGIN")
first = reader.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
writer.execute("INSERT INTO audit_log(message) VALUES ('提交前的读取')")
second = reader.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
print()
print("同一读事务内两次计数：", first, "->", second, "（快照不变，没有不可重复读和幻读）")
reader.execute("COMMIT")
print("读事务结束后再计数：", reader.execute(
    "SELECT COUNT(*) FROM audit_log"
).fetchone()[0])

print()
print("日志模式：", writer.execute("PRAGMA journal_mode").fetchone()[0])
reader.close()
writer.close()
for suffix in ("", "-wal", "-shm"):
    Path(str(db_path) + suffix).unlink(missing_ok=True)

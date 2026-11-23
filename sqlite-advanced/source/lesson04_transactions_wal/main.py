import sqlite3
from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
db_path = out / "lesson04.db"
for suffix in ("", "-wal", "-shm"):
    candidate = Path(str(db_path) + suffix)
    if candidate.exists():
        candidate.unlink()

conn = sqlite3.connect(db_path)
print("日志模式：", conn.execute("PRAGMA journal_mode=WAL").fetchone()[0])
conn.execute("PRAGMA busy_timeout=200")
conn.executescript(
    """
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        balance REAL NOT NULL CHECK (balance >= 0)
    );
    INSERT INTO accounts(id, name, balance) VALUES (1, '钱包', 1000);
    INSERT INTO accounts(id, name, balance) VALUES (2, '储蓄卡', 500);
    """
)


def transfer(amount):
    with conn:
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = 1", (amount,))
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = 2", (amount,))
        raise RuntimeError("模拟入账接口失败")


try:
    transfer(50)
except RuntimeError as error:
    print("捕获异常：", error)

print("转账失败后的余额：", conn.execute("SELECT id, balance FROM accounts ORDER BY id").fetchall())
conn.close()


reader = sqlite3.connect(db_path, isolation_level=None, timeout=0.2)
writer = sqlite3.connect(db_path, isolation_level=None, timeout=0.2)

writer.execute("BEGIN IMMEDIATE")
writer.execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
print("写连接看到：", writer.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0])

print("未提交时，另一个连接看到：", reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0])

try:
    reader.execute("BEGIN IMMEDIATE")
    print("第二个写事务拿到了锁（不应发生）")
except sqlite3.OperationalError as error:
    print("第二个写事务被阻塞：", error)
finally:
    if reader.in_transaction:
        reader.execute("ROLLBACK")

writer.execute("COMMIT")
print("提交后，另一个连接看到：", reader.execute("SELECT balance FROM accounts WHERE id = 1").fetchone()[0])

reader.close()
writer.close()


conn = sqlite3.connect(db_path)
print("journal_mode：", conn.execute("PRAGMA journal_mode").fetchone()[0])
print("wal_autocheckpoint：", conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0])
print("数据库文件：", sorted(path.name for path in out.glob("lesson04.db*")))

result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
print("检查点结果（busy, log, checkpointed）：", result)
conn.close()
print("关闭后的文件：", sorted(path.name for path in out.glob("lesson04.db*")))

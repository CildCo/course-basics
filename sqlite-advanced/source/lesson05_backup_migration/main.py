import sqlite3
from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

source_path = out / "lesson05_source.db"
backup_path = out / "lesson05_backup.db"
restored_path = out / "lesson05_restored.db"
for path in (source_path, backup_path, restored_path):
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        if candidate.exists():
            candidate.unlink()

conn = sqlite3.connect(source_path)
print("日志模式：", conn.execute("PRAGMA journal_mode=WAL").fetchone()[0])
conn.execute("PRAGMA user_version=1")
conn.executescript(
    """
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE
    );
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id),
        status TEXT NOT NULL,
        amount REAL NOT NULL,
        created_at TEXT NOT NULL
    );
    """
)

with conn:
    conn.executemany(
        "INSERT INTO users VALUES (?, ?, ?)",
        [(i, f"用户{i}", f"user{i}@example.com") for i in range(1, 21)],
    )
    rows = []
    for i in range(1, 501):
        rows.append(
            (
                i,
                i % 20 + 1,
                "paid" if i % 3 else "refunded",
                round((i % 80 + 20) / 7, 2),
                f"2026-{i % 12 + 1:02d}-{i % 28 + 1:02d}",
            )
        )
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", rows)

print("用户数：", conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
print("订单数：", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("user_version：", conn.execute("PRAGMA user_version").fetchone()[0])


target = sqlite3.connect(backup_path)
conn.backup(target)
target.close()

check = sqlite3.connect(backup_path)
print("备份完整性：", check.execute("PRAGMA integrity_check").fetchone()[0])
print("备份订单数：", check.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("备份大小：", backup_path.stat().st_size, "字节")
check.close()


conn.close()
for suffix in ("", "-wal", "-shm"):
    candidate = Path(str(source_path) + suffix)
    if candidate.exists():
        candidate.unlink()
print("源库还在吗：", source_path.exists())

backup_db = sqlite3.connect(backup_path)
recovered = sqlite3.connect(source_path)
backup_db.backup(recovered)
print("恢复后的订单数：", recovered.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("恢复后的完整性：", recovered.execute("PRAGMA integrity_check").fetchone()[0])
print("恢复后的 user_version：", recovered.execute("PRAGMA user_version").fetchone()[0])
recovered.close()
backup_db.close()
print("源库已重建：", source_path.exists())


conn = sqlite3.connect(source_path, isolation_level=None)
print("迁移前版本：", conn.execute("PRAGMA user_version").fetchone()[0])

conn.execute("PRAGMA foreign_keys=OFF")
conn.execute("BEGIN")
conn.execute("ALTER TABLE orders ADD COLUMN note TEXT NOT NULL DEFAULT ''")
conn.execute(
    """
    CREATE TABLE orders_new (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id),
        status TEXT NOT NULL CHECK (status IN ('paid', 'refunded')),
        amount REAL NOT NULL CHECK (amount >= 0),
        created_at TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT ''
    )
    """
)
conn.execute(
    """
    INSERT INTO orders_new(order_id, user_id, status, amount, created_at, note)
    SELECT order_id, user_id, status, amount, created_at, note FROM orders
    """
)
conn.execute("DROP TABLE orders")
conn.execute("ALTER TABLE orders_new RENAME TO orders")
conn.execute("CREATE INDEX idx_orders_user_created ON orders(user_id, created_at)")
conn.execute("PRAGMA user_version=2")
conn.execute("COMMIT")

print("迁移后版本：", conn.execute("PRAGMA user_version").fetchone()[0])
print("迁移后订单数：", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("完整性：", conn.execute("PRAGMA integrity_check").fetchone()[0])
print("外键检查：", conn.execute("PRAGMA foreign_key_check").fetchall())

try:
    conn.execute(
        "INSERT INTO orders(order_id, user_id, status, amount, created_at) VALUES (9999, 1, 'paid', -1, '2026-10-25')"
    )
    print("负金额写入成功（不应发生）")
except sqlite3.IntegrityError as error:
    print("负金额被拒绝：", error)

print()
print("orders 表结构：")
for column in conn.execute("PRAGMA table_info(orders)"):
    print(column)
conn.close()

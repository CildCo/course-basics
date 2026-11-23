from pathlib import Path


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

import sqlite3
import zipfile

db_path = out_dir / "app.db"
if db_path.exists():
    db_path.unlink()

connection = sqlite3.connect(db_path)
connection.executescript(
    """
    CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT);
    CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL);
    """
)
connection.executemany(
    "INSERT INTO users (id, name, city) VALUES (?, ?, ?)",
    [(i, f"user-{i:03d}", ["华东", "华南", "华北"][i % 3]) for i in range(1, 121)],
)
connection.executemany(
    "INSERT INTO orders (id, user_id, amount) VALUES (?, ?, ?)",
    [(i, i % 120 + 1, round(10 + i * 0.5, 2)) for i in range(1, 201)],
)
connection.commit()

print("用户数:", connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])
print("订单数:", connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0])


def stats(connection):
    users = connection.execute("SELECT COUNT(*), SUM(id) FROM users").fetchone()
    orders = connection.execute("SELECT COUNT(*), SUM(id) FROM orders").fetchone()
    return {"users": users, "orders": orders}


backup_dir = out_dir / "backup"
backup_dir.mkdir(exist_ok=True)
backup_path = backup_dir / "app-backup.db"
if backup_path.exists():
    backup_path.unlink()

source = sqlite3.connect(db_path)
target = sqlite3.connect(backup_path)
source.backup(target)
target.close()
source.close()

print("原库:", db_path.stat().st_size, "字节")
print("备份:", backup_path.stat().st_size, "字节")
print("备份统计:", stats(sqlite3.connect(backup_path)))


manifest = out_dir / "manifest.txt"
manifest.write_text("database=app.db\nrows=120\n", encoding="utf-8")

zip_path = out_dir / "backup.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.write(backup_path, backup_path.name)
    archive.write(manifest, manifest.name)

print("压缩包:", zip_path.name, zip_path.stat().st_size, "字节")
with zipfile.ZipFile(zip_path) as archive:
    for info in archive.infolist():
        print(" ", info.filename, info.file_size, "字节")


restore_dir = out_dir / "restore"
restore_dir.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path) as archive:
    archive.extractall(restore_dir)

restored_path = restore_dir / "app-backup.db"
restored = sqlite3.connect(restored_path)
print("恢复文件:", restored_path.name)
print("恢复统计:", stats(restored))
print("与原库一致:", stats(restored) == stats(sqlite3.connect(db_path)))


connection.execute("DELETE FROM users WHERE id > 100")
connection.commit()
print("误删后用户数:", connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])

recovered = sqlite3.connect(restored_path)
print("从备份恢复的用户数:", recovered.execute("SELECT COUNT(*) FROM users").fetchone()[0])
print("原库剩余用户数:", stats(connection)["users"][0])
print("恢复结果符合预期:", stats(recovered)["users"][0] == 120)

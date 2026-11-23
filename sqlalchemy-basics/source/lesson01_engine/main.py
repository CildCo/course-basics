from pathlib import Path
import tempfile

from sqlalchemy import create_engine, text

WORK = Path(tempfile.mkdtemp(prefix="sqlalchemy-basics-"))
DB_FILE = WORK / "demo.db"
engine = create_engine(f"sqlite:///{DB_FILE.as_posix()}")

print("方言:", engine.dialect.name)
print("驱动:", engine.driver)
print("连接串:", engine.url.render_as_string(hide_password=False))
print("数据库文件名:", DB_FILE.name)


with engine.connect() as conn:
    version = conn.execute(text("SELECT sqlite_version()")).scalar_one()
    answer = conn.execute(text("SELECT 1 + 1")).scalar_one()

print("SQLite 版本:", version)
print("1 + 1 =", answer)
print("连接池:", engine.pool.status())


with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """))
    conn.execute(
        text("INSERT INTO notes (title) VALUES (:title)"),
        [{"title": "第一条笔记"}, {"title": "第二条笔记"}],
    )

with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT id, title, created_at FROM notes ORDER BY id")
    ).all()

for row in rows:
    print(row.id, row.title, row.created_at)
print("文件大小:", DB_FILE.stat().st_size, "字节")


engine.dispose()
engine2 = create_engine(f"sqlite:///{DB_FILE.as_posix()}")
with engine2.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM notes")).scalar_one()

print("重新连接后的行数:", count)
engine2.dispose()

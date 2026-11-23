import sqlite3

conn = sqlite3.connect(":memory:", isolation_level=None)
conn.executescript(
    """
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE schema_migrations (
        version    INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL
    );
    """
)
conn.executemany(
    "INSERT INTO students VALUES (?, ?, ?, ?)",
    [
        (1, "林晓", "lin@example.com", "2026-09-01"),
        (2, "陈默", "Chen@Example.com", "2026-09-03"),
        (3, "周宁", "zhou@example.com", "2026-09-05"),
        (4, "许言", "xu@example.com", "2026-09-08"),
    ],
)
conn.execute("INSERT INTO schema_migrations VALUES (1, '2026-10-20T09:00:00')")

print("v1 行数：", conn.execute("SELECT COUNT(*) FROM students").fetchone()[0])
print("迁移版本：", conn.execute(
    "SELECT version, applied_at FROM schema_migrations ORDER BY version"
).fetchall())
print("列：", [row[1] for row in conn.execute("PRAGMA table_info(students)")])


conn.execute("BEGIN")
conn.execute("ALTER TABLE students ADD COLUMN major TEXT NOT NULL DEFAULT '未填写'")
conn.execute("UPDATE students SET major = '计算机' WHERE student_id IN (1, 2)")
conn.execute("UPDATE students SET major = '数据科学' WHERE student_id = 3")
conn.execute("INSERT INTO schema_migrations VALUES (2, '2026-10-22T10:30:00')")
conn.execute("COMMIT")

print("v2 列：", [row[1] for row in conn.execute("PRAGMA table_info(students)")])
print("v2 数据：", conn.execute(
    "SELECT student_id, name, major FROM students ORDER BY student_id"
).fetchall())


from pathlib import Path


def output_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        if (base / "assets").is_dir():
            folder = base / "output"
            folder.mkdir(exist_ok=True)
            return folder / name
    raise FileNotFoundError("assets")


backup_path = output_path("students-before-v3.db")
backup_path.unlink(missing_ok=True)
backup = sqlite3.connect(backup_path)
conn.backup(backup)
backup_row = backup.execute("SELECT COUNT(*) FROM students").fetchone()[0]
backup.close()
print("备份完成：", backup_path.name, "行数", backup_row)

conn.execute("BEGIN")
conn.execute(
    """
    CREATE TABLE students_new (
        student_id INTEGER PRIMARY KEY,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL UNIQUE,
        major      TEXT NOT NULL DEFAULT '未填写',
        created_at TEXT NOT NULL
    )
    """
)
conn.execute(
    """
    INSERT INTO students_new (student_id, name, email, major, created_at)
    SELECT student_id, name, lower(email), major, created_at FROM students
    """
)
conn.execute("DROP TABLE students")
conn.execute("ALTER TABLE students_new RENAME TO students")
conn.execute("INSERT INTO schema_migrations VALUES (3, '2026-10-25T11:00:00')")
conn.execute("COMMIT")

after_row = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
print("迁移后行数：", after_row, "，与备份一致：", after_row == backup_row)
print("邮箱已小写：", conn.execute(
    "SELECT student_id, email FROM students ORDER BY student_id"
).fetchall())

try:
    conn.execute("INSERT INTO students VALUES (5, '新同学', 'lin@example.com', '未填写', '2026-10-25')")
except sqlite3.IntegrityError as error:
    print("重复邮箱被拒绝：", error)

print("迁移记录：", conn.execute(
    "SELECT version FROM schema_migrations ORDER BY version"
).fetchall())
backup_path.unlink(missing_ok=True)

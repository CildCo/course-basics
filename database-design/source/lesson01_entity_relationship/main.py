import sqlite3
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


requirements = data_path("requirements.md").read_text(encoding="utf-8")
print(requirements.strip())


entities = [
    ("学生", ["学号", "姓名", "邮箱"], "学号"),
    ("课程", ["课程编号", "标题", "价格"], "课程编号"),
    ("课时", ["课时编号", "课程编号", "标题", "顺序"], "课时编号"),
    ("报名", ["学号", "课程编号", "报名时间"], "学号 + 课程编号"),
]

for name, attributes, key in entities:
    print(f"{name}: 属性 = {', '.join(attributes)}；候选键 = {key}")

print()
print("关系：")
print("  课程 1 —— N 课时")
print("  学生 N —— M 课程，通过报名表连接")


conn = sqlite3.connect(":memory:")
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(
    """
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY,
        student_no TEXT NOT NULL UNIQUE,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL UNIQUE
    );

    CREATE TABLE courses (
        course_id INTEGER PRIMARY KEY,
        title     TEXT NOT NULL,
        price     REAL NOT NULL CHECK (price >= 0)
    );

    CREATE TABLE lessons (
        lesson_id INTEGER PRIMARY KEY,
        course_id INTEGER NOT NULL REFERENCES courses(course_id),
        title     TEXT NOT NULL,
        position  INTEGER NOT NULL,
        UNIQUE (course_id, position)
    );

    CREATE TABLE enrollments (
        student_id  INTEGER NOT NULL REFERENCES students(student_id),
        course_id   INTEGER NOT NULL REFERENCES courses(course_id),
        enrolled_at TEXT NOT NULL,
        PRIMARY KEY (student_id, course_id)
    );
    """
)

conn.executemany(
    "INSERT INTO students VALUES (?, ?, ?, ?)",
    [
        (1, "S001", "林晓", "lin@example.com"),
        (2, "S002", "陈默", "chen@example.com"),
    ],
)
conn.executemany(
    "INSERT INTO courses VALUES (?, ?, ?)",
    [(1, "数据库设计入门", 99.0), (2, "SQL 进阶", 129.0)],
)
conn.executemany(
    "INSERT INTO lessons VALUES (?, ?, ?, ?)",
    [
        (1, 1, "从需求到表", 1),
        (2, 1, "主键与约束", 2),
        (3, 2, "窗口函数", 1),
        (4, 2, "执行计划", 2),
    ],
)
conn.executemany(
    "INSERT INTO enrollments VALUES (?, ?, ?)",
    [(1, 1, "2026-09-01"), (1, 2, "2026-09-03"), (2, 1, "2026-09-05")],
)

print("表：", [row[0] for row in conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
)])
print()
print("报名明细：")
for row in conn.execute(
    """
    SELECT s.name, c.title, e.enrolled_at
    FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN courses c ON c.course_id = e.course_id
    ORDER BY e.enrolled_at
    """
):
    print(f"  {row[0]} -> {row[1]}，{row[2]}")
print()
print("每门课的课时数：")
for row in conn.execute(
    """
    SELECT c.title, COUNT(l.lesson_id)
    FROM courses c
    LEFT JOIN lessons l ON l.course_id = c.course_id
    GROUP BY c.course_id
    ORDER BY c.course_id
    """
):
    print(f"  {row[0]}: {row[1]}")

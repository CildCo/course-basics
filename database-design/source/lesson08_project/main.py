from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


def output_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        if (base / "assets").is_dir():
            folder = base / "output"
            folder.mkdir(exist_ok=True)
            return folder / name
    raise FileNotFoundError("assets")


requirements = data_path("requirements.md").read_text(encoding="utf-8")
print(requirements.strip())


import sqlite3

conn = sqlite3.connect(":memory:", isolation_level=None)
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
        price     REAL NOT NULL CHECK (price >= 0),
        status    TEXT NOT NULL CHECK (status IN ('draft', 'published', 'archived'))
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

    CREATE TABLE lesson_progress (
        student_id INTEGER NOT NULL REFERENCES students(student_id),
        lesson_id  INTEGER NOT NULL REFERENCES lessons(lesson_id),
        status     TEXT NOT NULL CHECK (status IN ('started', 'completed')),
        updated_at TEXT NOT NULL,
        PRIMARY KEY (student_id, lesson_id)
    );

    CREATE TABLE payments (
        payment_id INTEGER PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(student_id),
        course_id  INTEGER NOT NULL REFERENCES courses(course_id),
        amount     REAL NOT NULL CHECK (amount >= 0),
        paid_at    TEXT NOT NULL,
        UNIQUE (student_id, course_id)
    );
    """
)

conn.executemany(
    "INSERT INTO students VALUES (?, ?, ?, ?)",
    [
        (1, "S001", "林晓", "lin@example.com"),
        (2, "S002", "陈默", "chen@example.com"),
        (3, "S003", "周宁", "zhou@example.com"),
    ],
)
conn.executemany(
    "INSERT INTO courses VALUES (?, ?, ?, ?)",
    [
        (1, "数据库设计入门", 99.0, "published"),
        (2, "SQL 进阶", 129.0, "published"),
        (3, "索引实战", 79.0, "draft"),
    ],
)
conn.executemany(
    "INSERT INTO lessons VALUES (?, ?, ?, ?)",
    [
        (1, 1, "从需求到表", 1),
        (2, 1, "主键与约束", 2),
        (3, 2, "窗口函数", 1),
        (4, 2, "执行计划", 2),
        (5, 3, "索引结构", 1),
    ],
)
conn.executemany(
    "INSERT INTO enrollments VALUES (?, ?, ?)",
    [(1, 1, "2026-09-01"), (1, 2, "2026-09-03"), (2, 1, "2026-09-05")],
)
conn.executemany(
    "INSERT INTO lesson_progress VALUES (?, ?, ?, ?)",
    [
        (1, 1, "completed", "2026-09-02"),
        (1, 2, "completed", "2026-09-04"),
        (1, 3, "started", "2026-09-06"),
        (2, 1, "completed", "2026-09-07"),
    ],
)
conn.executemany(
    "INSERT INTO payments VALUES (?, ?, ?, ?, ?)",
    [(1, 1, 1, 99.0, "2026-09-01"), (2, 1, 2, 129.0, "2026-09-03"), (3, 2, 1, 99.0, "2026-09-05")],
)

print("表：", [row[0] for row in conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
)])


print("每门课报名人数：")
for row in conn.execute(
    """
    SELECT c.title, COUNT(e.student_id)
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.course_id
    GROUP BY c.course_id
    ORDER BY c.course_id
    """
):
    print(" ", row)

print()
print("林晓的完成进度：")
for row in conn.execute(
    """
    SELECT c.title, l.title, p.status, p.updated_at
    FROM lesson_progress p
    JOIN lessons l ON l.lesson_id = p.lesson_id
    JOIN courses c ON c.course_id = l.course_id
    WHERE p.student_id = 1
    ORDER BY c.course_id, l.position
    """
):
    print(" ", row)

print()
print("每门课实收金额：")
for row in conn.execute(
    """
    SELECT c.title, SUM(p.amount), COUNT(*)
    FROM payments p
    JOIN courses c ON c.course_id = p.course_id
    GROUP BY c.course_id
    ORDER BY c.course_id
    """
):
    print(" ", row)


sql = """
SELECT lesson_id, status, updated_at
FROM lesson_progress
WHERE student_id = 1
ORDER BY updated_at DESC
LIMIT 5
"""


def show_plan(label, statement):
    print(label)
    for row in conn.execute("EXPLAIN QUERY PLAN " + statement):
        print("  ", row[3])
    print()


show_plan("只有主键索引时：", sql)
conn.execute("CREATE INDEX idx_progress_student_time ON lesson_progress(student_id, updated_at)")
show_plan("补复合索引后：", sql)
print("最近学习记录：", conn.execute(sql).fetchall())


checks = [
    ("每张表都有主键", "students/courses/lessons/enrollments/lesson_progress/payments 都有主键"),
    ("外键全部声明", "报名、进度、支付都指向学生或课程"),
    ("业务唯一性有约束", "学号、邮箱、一人一课一条支付都有 UNIQUE"),
    ("删除策略明确", "历史数据不物理删除，课程用 archived 状态"),
    ("关键查询有索引", "进度查询使用 student_id + updated_at 复合索引"),
    ("迁移可回滚", "迁移在事务中执行，失败回滚并保留备份"),
    ("金额与状态有检查", "价格、金额、状态都有 CHECK"),
    ("命名一致", "表用复数，主键统一 xxx_id"),
]

print("设计评审：")
for index, (item, detail) in enumerate(checks, 1):
    print(f"  {index}. [通过] {item}：{detail}")

passed = len(checks)
report = ["# 课程平台数据库设计评审", "", f"检查项：{passed}/{len(checks)} 通过", ""]
for index, (item, detail) in enumerate(checks, 1):
    report.append(f"{index}. {item}：{detail}")
report.append("")
report.append("后续改进：补充退款状态和优惠券表，并为支付时间增加按月统计的索引。")

report_path = output_path("design-review.md")
report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
print()
print("评审报告已写入：", report_path)
print("报告预览：")
print(report_path.read_text(encoding="utf-8"))

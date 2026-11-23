import sqlite3

conn = sqlite3.connect(":memory:", isolation_level=None)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(
    """
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY,
        student_no TEXT NOT NULL UNIQUE,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL UNIQUE,
        age        INTEGER CHECK (age BETWEEN 10 AND 100)
    );

    CREATE TABLE courses (
        course_id INTEGER PRIMARY KEY,
        title     TEXT NOT NULL,
        price     REAL NOT NULL CHECK (price >= 0)
    );

    CREATE TABLE enrollments (
        student_id INTEGER NOT NULL REFERENCES students(student_id),
        course_id  INTEGER NOT NULL REFERENCES courses(course_id),
        score      INTEGER CHECK (score BETWEEN 0 AND 100),
        PRIMARY KEY (student_id, course_id)
    );
    """
)

print("外键：", conn.execute("PRAGMA foreign_key_list(enrollments)").fetchall())
print()
print("报名表定义：")
print(conn.execute(
    "SELECT sql FROM sqlite_master WHERE name = 'enrollments'"
).fetchone()[0])


conn.execute("INSERT INTO students VALUES (1, 'S001', '林晓', 'lin@example.com', 20)")
conn.execute("INSERT INTO courses VALUES (1, '数据库设计入门', 99)")
conn.execute("INSERT INTO enrollments VALUES (1, 1, 88)")

bad_rows = [
    ("重复学号", "INSERT INTO students VALUES (2, 'S001', '陈默', 'chen@example.com', 21)"),
    ("姓名为空", "INSERT INTO students VALUES (3, 'S002', NULL, 'zhou@example.com', 22)"),
    ("年龄越界", "INSERT INTO students VALUES (4, 'S003', '周宁', 'zhou@example.com', 5)"),
    ("外键指向不存在的学生", "INSERT INTO enrollments VALUES (99, 1, 70)"),
    ("分数越界", "UPDATE enrollments SET score = 120 WHERE student_id = 1"),
]

for label, sql in bad_rows:
    try:
        conn.execute(sql)
        print(f"{label}：竟然写进去了")
    except sqlite3.IntegrityError as error:
        print(f"{label}：被拒绝 -> {error}")


conn.execute("INSERT INTO students VALUES (2, 'S002', '陈默', 'chen@example.com', 21)")
conn.execute("INSERT INTO enrollments VALUES (2, 1, 92)")
conn.execute("UPDATE enrollments SET score = 95 WHERE student_id = 2")

print("学生：", conn.execute("SELECT student_id, student_no, name FROM students ORDER BY student_id").fetchall())
print("报名与分数：", conn.execute("SELECT student_id, course_id, score FROM enrollments ORDER BY student_id").fetchall())
print("完整性检查：", conn.execute("PRAGMA integrity_check").fetchone()[0])

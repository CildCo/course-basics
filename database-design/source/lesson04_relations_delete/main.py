import sqlite3

conn = sqlite3.connect(":memory:", isolation_level=None)
conn.execute("PRAGMA foreign_keys = ON")
conn.executescript(
    """
    CREATE TABLE departments (
        dept_id INTEGER PRIMARY KEY,
        name    TEXT NOT NULL UNIQUE
    );

    CREATE TABLE employees (
        emp_id   INTEGER PRIMARY KEY,
        name     TEXT NOT NULL,
        dept_id  INTEGER NOT NULL REFERENCES departments(dept_id) ON DELETE RESTRICT,
        mentor_id INTEGER REFERENCES employees(emp_id) ON DELETE SET NULL
    );
    """
)

conn.executemany("INSERT INTO departments VALUES (?, ?)", [(1, "课程研发"), (2, "运营")])
conn.executemany(
    "INSERT INTO employees VALUES (?, ?, ?, ?)",
    [(1, "林晓", 1, None), (2, "陈默", 1, 1), (3, "周宁", 2, 1)],
)

try:
    conn.execute("DELETE FROM departments WHERE dept_id = 1")
except sqlite3.IntegrityError as error:
    print("删除仍被引用的部门：被拒绝 ->", error)

conn.execute("DELETE FROM employees WHERE emp_id = 1")
print("删除导师后：", conn.execute(
    "SELECT emp_id, name, mentor_id FROM employees ORDER BY emp_id"
).fetchall())


school = sqlite3.connect(":memory:", isolation_level=None)
school.execute("PRAGMA foreign_keys = ON")
school.executescript(
    """
    CREATE TABLE students (
        student_id INTEGER PRIMARY KEY,
        name       TEXT NOT NULL
    );

    CREATE TABLE courses (
        course_id INTEGER PRIMARY KEY,
        title     TEXT NOT NULL
    );

    CREATE TABLE enrollments (
        student_id  INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
        course_id   INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
        enrolled_at TEXT NOT NULL,
        PRIMARY KEY (student_id, course_id)
    );
    """
)
school.executemany("INSERT INTO students VALUES (?, ?)", [(1, "林晓"), (2, "陈默")])
school.executemany("INSERT INTO courses VALUES (?, ?)", [(1, "数据库设计入门"), (2, "SQL 进阶")])
school.executemany(
    "INSERT INTO enrollments VALUES (?, ?, ?)",
    [(1, 1, "2026-09-01"), (1, 2, "2026-09-03"), (2, 1, "2026-09-05")],
)

print("报名明细：")
for row in school.execute(
    """
    SELECT s.name, c.title, e.enrolled_at
    FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN courses c ON c.course_id = e.course_id
    ORDER BY e.enrolled_at
    """
):
    print(" ", row)

school.execute("DELETE FROM students WHERE student_id = 1")
print()
print("删除学生 1 后的报名数：", school.execute(
    "SELECT COUNT(*) FROM enrollments"
).fetchone()[0])
print("剩余报名：", school.execute(
    "SELECT student_id, course_id FROM enrollments"
).fetchall())


try:
    school.execute("INSERT INTO enrollments VALUES (2, 1, '2026-09-06')")
    print("重复报名：被主键拦住")
except sqlite3.IntegrityError as error:
    print("重复报名：被拒绝 ->", error)

print("学生 1 是否还在：", school.execute(
    "SELECT COUNT(*) FROM students WHERE student_id = 1"
).fetchone()[0])
print("课程 2 是否还在：", school.execute(
    "SELECT COUNT(*) FROM courses WHERE course_id = 2"
).fetchone()[0])

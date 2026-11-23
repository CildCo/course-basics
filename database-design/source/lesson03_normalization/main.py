import sqlite3

conn = sqlite3.connect(":memory:")
conn.executescript(
    """
    CREATE TABLE orders_wide (
        order_id       INTEGER PRIMARY KEY,
        customer_email TEXT NOT NULL,
        customer_name  TEXT NOT NULL,
        city           TEXT NOT NULL,
        product_name   TEXT NOT NULL,
        unit_price     REAL NOT NULL,
        quantity       INTEGER NOT NULL
    );
    """
)
conn.executemany(
    "INSERT INTO orders_wide VALUES (?, ?, ?, ?, ?, ?, ?)",
    [
        (1, "lin@example.com", "林晓", "杭州", "数据库设计入门", 99.0, 1),
        (2, "lin@example.com", "林晓", "杭州", "SQL 进阶", 129.0, 1),
        (3, "lin@example.com", "林晓", "杭州", "Python 入门", 89.0, 1),
        (4, "chen@example.com", "陈默", "成都", "数据库设计入门", 99.0, 2),
    ],
)

conn.execute("UPDATE orders_wide SET city = '上海' WHERE order_id = 1")
print("只改了一行之后：")
for row in conn.execute(
    "SELECT DISTINCT customer_email, city FROM orders_wide WHERE customer_email = 'lin@example.com'"
):
    print(" ", row)

print()
print("同一客户出现多个城市，说明同一个事实被存了多份。这就是更新异常。")


normalized = sqlite3.connect(":memory:")
normalized.execute("PRAGMA foreign_keys = ON")
normalized.executescript(
    """
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        email       TEXT NOT NULL UNIQUE,
        name        TEXT NOT NULL,
        city        TEXT NOT NULL
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name       TEXT NOT NULL,
        list_price REAL NOT NULL CHECK (list_price >= 0)
    );

    CREATE TABLE orders (
        order_id    INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        ordered_at  TEXT NOT NULL
    );

    CREATE TABLE order_items (
        order_id   INTEGER NOT NULL REFERENCES orders(order_id),
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        unit_price REAL NOT NULL,
        quantity   INTEGER NOT NULL,
        PRIMARY KEY (order_id, product_id)
    );
    """
)

normalized.executemany(
    "INSERT INTO customers VALUES (?, ?, ?, ?)",
    [(1, "lin@example.com", "林晓", "杭州"), (2, "chen@example.com", "陈默", "成都")],
)
normalized.executemany(
    "INSERT INTO products VALUES (?, ?, ?)",
    [(1, "数据库设计入门", 99.0), (2, "SQL 进阶", 129.0), (3, "Python 入门", 89.0)],
)
normalized.executemany(
    "INSERT INTO orders VALUES (?, ?, ?)",
    [(1, 1, "2026-09-01"), (2, 1, "2026-09-02"), (3, 1, "2026-09-03"), (4, 2, "2026-09-05")],
)
normalized.executemany(
    "INSERT INTO order_items VALUES (?, ?, ?, ?)",
    [(1, 1, 99.0, 1), (2, 2, 129.0, 1), (3, 3, 89.0, 1), (4, 1, 99.0, 2)],
)

normalized.execute("UPDATE customers SET city = '上海' WHERE customer_id = 1")
normalized.execute("UPDATE products SET list_price = 109 WHERE product_id = 1")

print("客户城市：", normalized.execute(
    "SELECT customer_id, name, city FROM customers ORDER BY customer_id"
).fetchall())
print()
print("订单明细（unit_price 是下单时的快照）：")
for row in normalized.execute(
    """
    SELECT o.order_id, c.name, p.name, i.unit_price, p.list_price, i.quantity
    FROM order_items i
    JOIN orders o ON o.order_id = i.order_id
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN products p ON p.product_id = i.product_id
    ORDER BY o.order_id
    """
):
    print(f"  订单{row[0]} {row[1]} 买 {row[2]}，成交价 {row[3]}，当前标价 {row[4]}，数量 {row[5]}")


print("宽表：", conn.execute(
    "SELECT COUNT(*), COUNT(DISTINCT customer_email) FROM orders_wide"
).fetchone(), "（行数, 客户数）")
print("拆分后客户表：", normalized.execute(
    "SELECT COUNT(*) FROM customers"
).fetchone()[0], "行")
print("同一客户城市数：", normalized.execute(
    "SELECT customer_id, COUNT(DISTINCT city) FROM customers GROUP BY customer_id"
).fetchall())
print("订单金额快照是否保留：", normalized.execute(
    "SELECT unit_price, list_price FROM order_items JOIN products USING (product_id) WHERE order_id = 2"
).fetchone())

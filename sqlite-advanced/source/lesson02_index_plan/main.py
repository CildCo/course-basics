import sqlite3
import time
from pathlib import Path

conn = sqlite3.connect(":memory:")
conn.execute(
    """
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        amount REAL NOT NULL,
        created_at TEXT NOT NULL
    )
    """
)

rows = []
for i in range(1, 60001):
    rows.append(
        (
            i,
            i % 500,
            "paid" if i % 4 else "refunded",
            round((i % 90 + 10) / 3, 2),
            f"2026-{i % 12 + 1:02d}-{i % 28 + 1:02d}",
        )
    )
with conn:
    conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", rows)


def query_time(sql, params, repeat=30):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        conn.execute(sql, params).fetchall()
        samples.append((time.perf_counter() - start) * 1000)
    samples.sort()
    return samples[len(samples) // 2]


def show_plan(label, sql, params=()):
    print(label)
    for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params):
        print("  ", row[3])
    print()


sql = "SELECT order_id, amount FROM orders WHERE customer_id = ? AND status = ?"
params = (42, "paid")

print("订单行数：", conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("命中行数：", len(conn.execute(sql, params).fetchall()))
show_plan("建索引前：", sql, params)
before = query_time(sql, params)
print(f"建索引前中位耗时：{before:.2f} ms")


conn.execute(
    "CREATE INDEX idx_orders_customer_status ON orders(customer_id, status)"
)
show_plan("建索引后：", sql, params)

after = query_time(sql, params)
print(f"建索引后中位耗时：{after:.2f} ms")
print(f"提速倍数：{before / after:.1f} 倍")
print()
print("索引列表：", conn.execute("PRAGMA index_list(orders)").fetchall())


import struct
import zlib

FONT = {
    "A": ("01110", "10001", "11111", "10001", "10001"),
    "B": ("11110", "10001", "11110", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "11110", "10000", "11111"),
    "F": ("11111", "10000", "11110", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10011", "01110"),
    "H": ("10001", "10001", "11111", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "11100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "11110", "10000", "10000"),
    "Q": ("01110", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "11110", "10010", "10001"),
    "S": ("01111", "10000", "01110", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10101", "11011", "10001"),
    "X": ("10001", "01010", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100"),
    "Z": ("11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10011", "10101", "11001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00010", "00100", "11111"),
    "3": ("11110", "00001", "01110", "00001", "11110"),
    "4": ("00010", "00110", "01010", "11111", "00010"),
    "5": ("11111", "10000", "11110", "00001", "11110"),
    "6": ("01110", "10000", "11110", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000"),
    "8": ("01110", "10001", "01110", "10001", "01110"),
    "9": ("01110", "10001", "01111", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00100"),
    "-": ("00000", "00000", "11111", "00000", "00000"),
    "(": ("00010", "00100", "00100", "00100", "00010"),
    ")": ("01000", "00100", "00100", "00100", "01000"),
}


def draw_rect(pixels, x0, y0, x1, y1, color):
    width = len(pixels[0]) // 3
    x0, x1 = max(0, x0), min(width, x1)
    y0, y1 = max(0, y0), min(len(pixels), y1)
    block = bytes(color) * max(0, x1 - x0)
    for y in range(y0, y1):
        pixels[y][x0 * 3:x1 * 3] = block


def draw_text(pixels, x, y, text, scale, color):
    cursor = x
    for char in text.upper():
        pattern = FONT.get(char)
        if pattern:
            for row_index, row in enumerate(pattern):
                for col_index, bit in enumerate(row):
                    if bit == "1":
                        draw_rect(
                            pixels,
                            cursor + col_index * scale,
                            y + row_index * scale,
                            cursor + (col_index + 1) * scale,
                            y + (row_index + 1) * scale,
                            color,
                        )
        cursor += 6 * scale


def png_bytes(pixels):
    height = len(pixels)
    width = len(pixels[0]) // 3
    raw = b"".join(bytes([0]) + bytes(row) for row in pixels)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    signature = bytes([137, 80, 78, 71, 13, 10, 26, 10])
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return signature + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")


class Png:
    def __init__(self, data):
        self.data = data

    def _repr_png_(self):
        return self.data


def bar_chart(path, title, rows):
    width, height = 720, 360
    background = (248, 247, 243)
    pixels = [bytearray(background * width) for _ in range(height)]
    draw_text(pixels, 40, 26, title, 2, (40, 40, 40))
    draw_rect(pixels, 198, 70, 202, 300, (170, 170, 170))
    maximum = max(value for _, value, _ in rows) or 1
    for index, (label, value, color) in enumerate(rows):
        top = 95 + index * 100
        draw_text(pixels, 40, top + 12, label, 2, (55, 55, 55))
        bar_width = max(6, int((width - 300) * value / maximum))
        draw_rect(pixels, 205, top, 205 + bar_width, top + 44, color)
        draw_text(pixels, 215 + bar_width, top + 14, f"{value:.2f}", 2, (55, 55, 55))
    path.write_bytes(png_bytes(pixels))
    return Png(path.read_bytes())


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
rows = [
    ("NO INDEX", before, (196, 92, 74)),
    ("INDEX", after, (52, 122, 96)),
]
bar_chart(out / "index-timing.png", "QUERY TIME (MS)", rows)

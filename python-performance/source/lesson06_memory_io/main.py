import sys
import time

samples = [0, 2**64, "python", "性能分析", [], [0] * 100, {}, {"a": 1}]
for value in samples:
    label = type(value).__name__
    print(f"{label:5s} {sys.getsizeof(value):6d} 字节")


import tracemalloc

tracemalloc.start()
rows = [{"id": index, "value": index * 2} for index in range(100_000)]
current, peak = tracemalloc.get_traced_memory()
print("当前:", round(current / 1024 / 1024, 2), "MB")
print("峰值:", round(peak / 1024 / 1024, 2), "MB")
del rows
tracemalloc.stop()


import csv
from pathlib import Path

from pathlib import Path

def data_path(name):
    here = Path.cwd()
    bases = [here, here.parent, here.parent.parent]
    try:
        base = Path(__file__).resolve().parent
        bases = [base, base.parent, base.parent.parent] + bases
    except NameError:
        pass
    for base in bases:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

DATA = data_path("orders.csv")
print("文件大小:", round(DATA.stat().st_size / 1024, 1), "KB")


def read_all_rows():
    with DATA.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

def stream_rows():
    total = 0
    with DATA.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            total += int(row["units"])
    return total

tracemalloc.start()
start = time.perf_counter()
rows = read_all_rows()
all_seconds = time.perf_counter() - start
_, all_peak = tracemalloc.get_traced_memory()
del rows

tracemalloc.reset_peak()
start = time.perf_counter()
units_total = stream_rows()
stream_seconds = time.perf_counter() - start
_, stream_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print("整体读取:", round(all_seconds * 1000, 1), "毫秒，峰值", round(all_peak / 1024 / 1024, 2), "MB")
print("流式读取:", round(stream_seconds * 1000, 1), "毫秒，峰值", round(stream_peak / 1024, 1), "KB")
print("内存倍数:", round(all_peak / max(stream_peak, 1), 1), "倍")
print("units 合计:", units_total)


def read_text_all():
    return DATA.read_text(encoding="utf-8")

def read_text_chunks(chunk_size=8192):
    pieces = 0
    with DATA.open(encoding="utf-8") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            pieces += 1
    return pieces

tracemalloc.start()
start = time.perf_counter()
text = read_text_all()
text_seconds = time.perf_counter() - start
_, text_peak = tracemalloc.get_traced_memory()
del text

tracemalloc.reset_peak()
start = time.perf_counter()
pieces = read_text_chunks()
chunk_seconds = time.perf_counter() - start
_, chunk_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print("一次性读取:", round(text_seconds * 1000, 2), "毫秒，峰值", round(text_peak / 1024, 1), "KB")
print("分块读取:", round(chunk_seconds * 1000, 2), "毫秒，峰值", round(chunk_peak / 1024, 1), "KB，块数", pieces)

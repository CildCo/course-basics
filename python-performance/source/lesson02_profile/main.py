import cProfile
import csv
import io
import pstats
import time
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

def load_orders(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

def normalize_region(value):
    return value.strip().lower()

def line_total(row):
    return int(row["units"]) * float(row["unit_price"])

def group_totals(rows):
    totals = {}
    for row in rows:
        key = (normalize_region(row["region"]), row["category"])
        totals[key] = totals.get(key, 0.0) + line_total(row)
    return totals

def top_entries(totals, count=5):
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:count]

orders = load_orders(data_path("orders.csv"))
print("订单行数:", len(orders))


def run_report():
    for _ in range(10):
        totals = group_totals(orders)
    return top_entries(totals)

profile = cProfile.Profile()
result = profile.runcall(run_report)

stream = io.StringIO()
stats = pstats.Stats(profile, stream=stream)
stats.strip_dirs().sort_stats("cumulative").print_stats(10)
print(stream.getvalue())
print("前 3 项:", result[:3])


stream = io.StringIO()
stats = pstats.Stats(profile, stream=stream)
stats.strip_dirs().sort_stats("tottime").print_stats(8)
print(stream.getvalue())


REGION_CACHE = {value: value.strip().lower() for value in {row["region"] for row in orders}}

def group_totals_cached(rows):
    totals = {}
    for row in rows:
        key = (REGION_CACHE[row["region"]], row["category"])
        totals[key] = totals.get(key, 0.0) + int(row["units"]) * float(row["unit_price"])
    return totals

def timed(func, rows, times=5):
    start = time.perf_counter()
    for _ in range(times):
        func(rows)
    return time.perf_counter() - start

print("group_totals:", round(timed(group_totals, orders), 3), "秒")
print("group_totals_cached:", round(timed(group_totals_cached, orders), 3), "秒")

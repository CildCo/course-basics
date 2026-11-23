import time
import timeit
from pathlib import Path

import numpy as np
import pandas as pd

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

PY_VALUES = list(range(1_000_000))
ARRAY = np.arange(1_000_000, dtype=np.float64)

def python_multiply():
    return [value * 2.5 for value in PY_VALUES]

def numpy_multiply():
    return ARRAY * 2.5

loop_time = min(timeit.repeat(python_multiply, repeat=3, number=1))
numpy_time = min(timeit.repeat(numpy_multiply, repeat=3, number=1))
print("Python 循环:", round(loop_time * 1000, 2), "毫秒")
print("NumPy 向量化:", round(numpy_time * 1000, 2), "毫秒")
print("倍数:", round(loop_time / numpy_time, 1), "倍")
print("首个结果一致:", python_multiply()[0] == numpy_multiply()[0])


df = pd.read_csv(data_path("orders.csv"))
print("行数:", len(df))
print(df.dtypes.to_string())
df.head()


def totals_iterrows(frame):
    total = 0.0
    for _, row in frame.iterrows():
        total += row["units"] * row["unit_price"]
    return total

def totals_vectorized(frame):
    return float((frame["units"] * frame["unit_price"]).sum())

start = time.perf_counter()
iter_total = totals_iterrows(df)
iter_seconds = time.perf_counter() - start

start = time.perf_counter()
vector_total = totals_vectorized(df)
vector_seconds = time.perf_counter() - start

print("iterrows:", round(iter_total, 2), "耗时", round(iter_seconds * 1000, 1), "毫秒")
print("向量化:", round(vector_total, 2), "耗时", round(vector_seconds * 1000, 2), "毫秒")
print("倍数:", round(iter_seconds / vector_seconds, 1), "倍")


def region_loop(frame):
    totals = {}
    for region, units, price in zip(frame["region"], frame["units"], frame["unit_price"]):
        totals[region] = totals.get(region, 0.0) + units * price
    return totals

start = time.perf_counter()
loop_totals = region_loop(df)
loop_seconds = time.perf_counter() - start

start = time.perf_counter()
series_totals = (df["units"] * df["unit_price"]).groupby(df["region"]).sum()
group_seconds = time.perf_counter() - start

print("循环结果:", {key: round(value, 2) for key, value in sorted(loop_totals.items())})
print("groupby 结果:", {key: round(float(value), 2) for key, value in series_totals.sort_index().items()})
print("耗时倍数:", round(loop_seconds / group_seconds, 1), "倍")

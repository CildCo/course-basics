import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import sys
from pathlib import Path

def find_assets():
    here = Path.cwd()
    candidates = [here, here.parent, here.parent.parent]
    try:
        base = Path(__file__).resolve().parent
        candidates = [base, base.parent] + candidates
    except NameError:
        pass
    for base in candidates:
        folder = base / "assets"
        if folder.is_dir():
            return folder
    raise FileNotFoundError("assets")

ASSETS = find_assets()
if str(ASSETS) not in sys.path:
    sys.path.append(str(ASSETS))

from mp_worker import sum_squares

LIMITS = [3_000_000] * 12
print("任务数:", len(LIMITS), "| 逻辑 CPU:", os.cpu_count())


def run_serial(limits):
    return [sum_squares(limit) for limit in limits]

if __name__ == "__main__":
    start = time.perf_counter()
    serial_result = run_serial(LIMITS)
    serial_seconds = time.perf_counter() - start
    print("单进程:", round(serial_seconds, 2), "秒")


def run_pool(limits):
    with ProcessPoolExecutor(max_workers=4) as pool:
        return list(pool.map(sum_squares, limits))

if __name__ == "__main__":
    start = time.perf_counter()
    pool_result = run_pool(LIMITS)
    pool_seconds = time.perf_counter() - start
    print("4 进程:", round(pool_seconds, 2), "秒")
    print("结果一致:", serial_result == pool_result)
    print("加速比:", round(serial_seconds / pool_seconds, 2), "倍")


print("逻辑 CPU:", os.cpu_count())
print("建议 worker 数不超过:", os.cpu_count())
print("本次使用 worker 数: 4")

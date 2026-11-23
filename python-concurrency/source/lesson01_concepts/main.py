import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
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

from mp_worker import sleep_task

TASKS = list(range(8))
if __name__ == "__main__":
    print("任务数:", len(TASKS), "| 每个任务模拟 I/O 0.2 秒")


def run_sequential(tasks):
    return [sleep_task(task_id) for task_id in tasks]

if __name__ == "__main__":
    start = time.perf_counter()
    sequential_result = run_sequential(TASKS)
    sequential_seconds = time.perf_counter() - start
    print("顺序:", round(sequential_seconds, 3), "秒")


def run_threads(tasks):
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(sleep_task, tasks))

if __name__ == "__main__":
    start = time.perf_counter()
    thread_result = run_threads(TASKS)
    thread_seconds = time.perf_counter() - start
    print("线程:", round(thread_seconds, 3), "秒")


def run_processes(tasks):
    with ProcessPoolExecutor(max_workers=4) as pool:
        return list(pool.map(sleep_task, tasks))

async def async_task(task_id):
    await asyncio.sleep(0.2)
    return task_id * 2

async def run_async(tasks):
    return await asyncio.gather(*(async_task(task_id) for task_id in tasks))

async def main():
    global process_result, process_seconds, async_result, async_seconds
    if __name__ != "__main__":
        return

    start = time.perf_counter()
    process_result = run_processes(TASKS)
    process_seconds = time.perf_counter() - start
    print("进程:", round(process_seconds, 3), "秒")

    start = time.perf_counter()
    async_result = await run_async(TASKS)
    async_seconds = time.perf_counter() - start
    print("异步:", round(async_seconds, 3), "秒")
    print("结果一致:", sequential_result == thread_result == process_result == async_result)

asyncio.run(main())


if __name__ == "__main__":
    summary = [
        ("顺序", sequential_seconds),
        ("线程", thread_seconds),
        ("进程", process_seconds),
        ("异步", async_seconds),
    ]
    base = sequential_seconds
    for name, seconds in summary:
        print(f"{name}: {seconds:.3f} 秒，约为顺序的 {seconds / base:.2f} 倍")

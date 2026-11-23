"""并发课程在子进程中执行的 worker。

Windows 使用 spawn 启动子进程，函数必须放在可以导入的模块里，
不能定义在 Notebook 或 __main__ 中。
"""
from __future__ import annotations

import time


def sleep_task(task_id: int, seconds: float = 0.2) -> int:
    """模拟一次 I/O 任务，返回处理后的任务编号。"""
    time.sleep(seconds)
    return task_id * 2


def sum_squares(limit: int) -> int:
    """CPU 密集任务：累加平方，用来观察多进程加速。"""
    total = 0
    for value in range(limit):
        total += value * value
    return total

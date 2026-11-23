import os
import threading
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

print("当前进程 PID：", os.getpid())
print("父进程 PID：", os.getppid())
print("当前线程：", threading.current_thread().name)
print("活跃线程数：", threading.active_count())
print("线程列表：", [thread.name for thread in threading.enumerate()])
print("CPU 逻辑核心：", os.cpu_count())


process_a = {"name": "A", "memory": {"count": 0}}
process_b = {"name": "B", "memory": {"count": 0}}


def bump(memory, times):
    for _ in range(times):
        memory["count"] += 1


threads = [
    threading.Thread(target=bump, args=(process_a["memory"], 3), name=f"A-{index}")
    for index in (1, 2)
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("进程 A 的计数：", process_a["memory"]["count"])
print("进程 B 的计数：", process_b["memory"]["count"])
print("两个进程的内存是同一份吗：", process_a["memory"] is process_b["memory"])
print("线程名字：", [thread.name for thread in threads])


from dataclasses import dataclass


@dataclass
class Process:
    pid: int
    name: str
    state: str = "NEW"


flow = [
    ("NEW", "READY"),
    ("READY", "RUNNING"),
    ("RUNNING", "WAITING"),
    ("WAITING", "READY"),
    ("READY", "RUNNING"),
    ("RUNNING", "TERMINATED"),
]

process = Process(1001, "demo")
history = [process.state]
for source, target in flow:
    assert process.state == source
    process.state = target
    history.append(process.state)

print("状态轨迹：", " -> ".join(history))
print("进程是否结束：", process.state == "TERMINATED")
print("迁移次数：", len(flow))

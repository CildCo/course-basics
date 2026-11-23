import os
import subprocess
import sys

parent_pid = os.getpid()
result = subprocess.run(
    [sys.executable, "-c", "import os; print(os.getpid())"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    check=True,
)
child_pid = int(result.stdout.strip())

print("父子 PID 不同：", parent_pid != child_pid)
print("子进程退出码：", result.returncode)


failed = subprocess.run([sys.executable, "-c", "raise SystemExit(3)"])
print("非零退出码：", failed.returncode)


import threading

results = []
lock = threading.Lock()

def worker(name, count):
    for index in range(count):
        with lock:
            results.append(f"{name}-{index}")

main_thread = threading.current_thread()
threads = [
    threading.Thread(target=worker, args=(f"t{number}", 3), name=f"worker-{number}")
    for number in (1, 2)
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("主线程：", main_thread.name)
print("工作线程：", [thread.name for thread in threads])
print("线程都结束了：", all(not thread.is_alive() for thread in threads))
print("结果数量：", len(results))
print("排序后的结果：", sorted(results))

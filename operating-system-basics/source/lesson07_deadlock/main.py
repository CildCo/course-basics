import threading
import time
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


left = threading.Lock()
right = threading.Lock()
gate = threading.Barrier(2)
events = []
events_lock = threading.Lock()


def record(message):
    with events_lock:
        events.append(message)


def worker_first(name, first, second, first_label, second_label):
    with first:
        record(f"{name} 持有{first_label}")
        gate.wait()
        acquired = second.acquire(timeout=0.2)
        if acquired:
            record(f"{name} 又拿到{second_label}")
            second.release()
        else:
            record(f"{name} 等不到{second_label}，判定为死锁")
    record(f"{name} 释放{first_label}")


threads = [
    threading.Thread(target=worker_first,
                     args=("线程 A", left, right, "锁 L", "锁 R")),
    threading.Thread(target=worker_first,
                     args=("线程 B", right, left, "锁 R", "锁 L")),
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join(timeout=2)

for message in events:
    print(message)
print("是否出现循环等待：", any("判定为死锁" in message for message in events))
print("线程是否都结束：", all(not thread.is_alive() for thread in threads))


locks = {"L": threading.Lock(), "R": threading.Lock()}
completed = []
completed_lock = threading.Lock()


def worker_ordered(name, first, second):
    order = sorted([first, second])
    with locks[order[0]]:
        time.sleep(0.02)
        with locks[order[1]]:
            with completed_lock:
                completed.append(name)


threads = [
    threading.Thread(target=worker_ordered, args=("线程 A", "L", "R")),
    threading.Thread(target=worker_ordered, args=("线程 B", "R", "L")),
]
gate.reset()
for thread in threads:
    thread.start()
for thread in threads:
    thread.join(timeout=2)

print("完成的任务：", sorted(completed))
print("两个线程都完成：", len(completed) == 2)


available = [3, 3, 2]
maximum = [
    [7, 5, 3],
    [3, 2, 2],
    [9, 0, 2],
    [2, 2, 2],
    [4, 3, 3],
]
allocation = [
    [0, 1, 0],
    [2, 0, 0],
    [3, 0, 2],
    [2, 1, 1],
    [0, 0, 2],
]
need = [
    [maximum[row][column] - allocation[row][column] for column in range(3)]
    for row in range(len(maximum))
]


def safety(available_now, need_now, allocation_now):
    work = list(available_now)
    finish = [False] * len(need_now)
    sequence = []
    while len(sequence) < len(need_now):
        progressed = False
        for index in range(len(need_now)):
            if finish[index]:
                continue
            if all(need_now[index][column] <= work[column] for column in range(3)):
                work = [
                    work[column] + allocation_now[index][column]
                    for column in range(3)
                ]
                finish[index] = True
                sequence.append(f"P{index}")
                progressed = True
        if not progressed:
            break
    return sequence, finish


print("Need 矩阵：")
for index, row in enumerate(need):
    print(f"  P{index}: {row}")

sequence, finish = safety(available, need, allocation)
print("当前安全序列：", " -> ".join(sequence))
print("是否安全：", all(finish))


def request_resources(process_index, request):
    if not all(
        request[column] <= need[process_index][column]
        and request[column] <= available[column]
        for column in range(3)
    ):
        return None
    trial_available = [
        available[column] - request[column] for column in range(3)
    ]
    trial_allocation = [row[:] for row in allocation]
    trial_need = [row[:] for row in need]
    for column in range(3):
        trial_allocation[process_index][column] += request[column]
        trial_need[process_index][column] -= request[column]
    trial_sequence, trial_finish = safety(
        trial_available, trial_need, trial_allocation
    )
    return trial_sequence, trial_finish


for label, process_index, request in [
    ("P1 申请 [1, 0, 0]", 1, [1, 0, 0]),
    ("P0 申请 [3, 3, 0]", 0, [3, 3, 0]),
]:
    result = request_resources(process_index, request)
    if result is None:
        print(label, "超过 Need 或可用资源，直接拒绝")
    else:
        trial_sequence, trial_finish = result
        print(label, "后安全序列：", " -> ".join(trial_sequence))
        print("  是否安全：", all(trial_finish))

import threading
import time
from collections import deque
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


print("== 手动展开一次丢失更新 ==")
state = {"balance": 100}
first_read = state["balance"]
second_read = state["balance"]
state["balance"] = first_read - 40
state["balance"] = second_read - 30
print("两次分别取 40 和 30，期望余额 30，实际余额：", state["balance"])


THREADS = 4
INCREMENTS = 30000

counter = {"value": 0}
gate = threading.Barrier(THREADS)


def add_unsafe():
    gate.wait()
    for _ in range(INCREMENTS):
        value = counter["value"]
        time.sleep(0)
        counter["value"] = value + 1


workers = [threading.Thread(target=add_unsafe) for _ in range(THREADS)]
begin = time.perf_counter()
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
elapsed = time.perf_counter() - begin

print("目标值：", THREADS * INCREMENTS)
print("实际值：", counter["value"])
print("是否发生丢更新：", counter["value"] < THREADS * INCREMENTS)
print("耗时：", round(elapsed, 3), "秒")


counter = {"value": 0}
lock = threading.Lock()
gate = threading.Barrier(THREADS)


def add_locked():
    gate.wait()
    for _ in range(INCREMENTS):
        with lock:
            counter["value"] += 1


workers = [threading.Thread(target=add_locked) for _ in range(THREADS)]
begin = time.perf_counter()
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
elapsed = time.perf_counter() - begin

print("加锁后的值：", counter["value"])
print("是否等于目标值：", counter["value"] == THREADS * INCREMENTS)
print("耗时：", round(elapsed, 3), "秒")


class BoundedBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = deque()
        self.condition = threading.Condition()

    def put(self, item):
        with self.condition:
            while len(self.items) >= self.capacity:
                self.condition.wait()
            self.items.append(item)
            self.condition.notify_all()

    def get(self):
        with self.condition:
            while not self.items:
                self.condition.wait()
            item = self.items.popleft()
            self.condition.notify_all()
            return item


buffer = BoundedBuffer(3)
produced = []
consumed = []
record_lock = threading.Lock()


def producer():
    for item in range(1, 7):
        buffer.put(item)
        with record_lock:
            produced.append(item)


def consumer():
    for _ in range(6):
        item = buffer.get()
        with record_lock:
            consumed.append(item)


threads = [
    threading.Thread(target=producer, name="生产者"),
    threading.Thread(target=consumer, name="消费者"),
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print("生产：", produced)
print("消费：", consumed)
print("顺序一致：", produced == consumed)

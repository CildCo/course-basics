import threading
import time

THREADS = 4
INCREMENTS = 30_000

class Counter:
    def __init__(self):
        self.value = 0

def increment_unsafe(counter, barrier):
    barrier.wait()
    for _ in range(INCREMENTS):
        current = counter.value
        time.sleep(0)
        counter.value = current + 1


counter = Counter()
barrier = threading.Barrier(THREADS)
workers = [
    threading.Thread(target=increment_unsafe, args=(counter, barrier))
    for _ in range(THREADS)
]

start = time.perf_counter()
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
print("无锁最终值:", counter.value)
print("目标值:", THREADS * INCREMENTS)
print("耗时:", round(time.perf_counter() - start, 3), "秒")


def increment_locked(counter, lock, barrier):
    barrier.wait()
    for _ in range(INCREMENTS):
        with lock:
            counter.value += 1

counter = Counter()
lock = threading.Lock()
barrier = threading.Barrier(THREADS)
workers = [
    threading.Thread(target=increment_locked, args=(counter, lock, barrier))
    for _ in range(THREADS)
]

start = time.perf_counter()
for worker in workers:
    worker.start()
for worker in workers:
    worker.join()
print("有锁最终值:", counter.value)
print("目标值:", THREADS * INCREMENTS)
print("耗时:", round(time.perf_counter() - start, 3), "秒")


results = []
for _ in range(3):
    counter = Counter()
    barrier = threading.Barrier(THREADS)
    workers = [
        threading.Thread(target=increment_unsafe, args=(counter, barrier))
        for _ in range(THREADS)
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    results.append(counter.value)

print("三次无锁结果:", results)
print("目标值:", THREADS * INCREMENTS)

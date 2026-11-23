import queue
import threading
import time

tasks = queue.Queue(maxsize=5)
processed = []

def producer(name, count):
    for index in range(count):
        item = f"{name}-{index}"
        tasks.put(item)
        time.sleep(0.01)
    tasks.put(None)

def consumer(name):
    while True:
        item = tasks.get()
        try:
            if item is None:
                break
            time.sleep(0.01)
            processed.append((name, item))
        finally:
            tasks.task_done()


producers = [threading.Thread(target=producer, args=(f"P{index}", 10)) for index in range(2)]
consumers = [threading.Thread(target=consumer, args=(f"C{index}",)) for index in range(2)]

start = time.perf_counter()
for thread in producers + consumers:
    thread.start()
for thread in producers:
    thread.join()
for thread in consumers:
    thread.join()
elapsed = time.perf_counter() - start

print("处理数量:", len(processed))
counts = {name: sum(1 for worker, _ in processed if worker == name) for name in ("C0", "C1")}
print("各消费者:", counts)
print("耗时:", round(elapsed, 2), "秒")


print("队列剩余:", tasks.qsize())
print("处理总数:", len(processed))
print("消费者是否都已退出:", not any(thread.is_alive() for thread in consumers))

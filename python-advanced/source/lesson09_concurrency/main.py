import threading

results = []
lock = threading.Lock()

def worker(number):
    with lock:
        results.append(number * 2)

threads = [threading.Thread(target=worker, args=(n,)) for n in range(1, 4)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()

print(sorted(results))


import asyncio

async def fetch(name, delay):
    await asyncio.sleep(delay)
    return f"{name} 完成"

async def main():
    results = await asyncio.gather(
        fetch("A", 0.02),
        fetch("B", 0.01),
    )
    print(results)

asyncio.run(main())

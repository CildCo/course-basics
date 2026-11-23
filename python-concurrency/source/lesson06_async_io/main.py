import asyncio
import time

async def fetch(item, delay=0.2):
    await asyncio.sleep(delay)
    return f"结果-{item}"

ITEMS = list(range(6))
print("请求数:", len(ITEMS), "| 每次模拟 0.2 秒")


async def run_sequential(items):
    results = []
    for item in items:
        results.append(await fetch(item))
    return results

async def main():
    global sequential, sequential_seconds
    start = time.perf_counter()
    sequential = await run_sequential(ITEMS)
    sequential_seconds = time.perf_counter() - start
    print("顺序 await:", round(sequential_seconds, 2), "秒")
    print("前两个结果:", sequential[:2])

asyncio.run(main())


async def run_gather(items):
    return await asyncio.gather(*(fetch(item) for item in items))

async def main():
    start = time.perf_counter()
    concurrent = await run_gather(ITEMS)
    concurrent_seconds = time.perf_counter() - start
    print("gather:", round(concurrent_seconds, 2), "秒")
    print("结果一致:", sequential == concurrent)
    print("倍数:", round(sequential_seconds / concurrent_seconds, 1), "倍")

asyncio.run(main())


async def main():
    delays = [0.1, 0.2, 0.3, 0.4]
    start = time.perf_counter()
    results = await asyncio.gather(*(fetch(index, delay) for index, delay in enumerate(delays)))
    print("结果:", results)
    print("总耗时:", round(time.perf_counter() - start, 2), "秒")

asyncio.run(main())

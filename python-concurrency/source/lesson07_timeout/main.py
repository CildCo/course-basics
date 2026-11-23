import asyncio
import time

async def slow_task(seconds):
    await asyncio.sleep(seconds)
    return "完成" 


async def main():
    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(slow_task(1.0), timeout=0.3)
        print("结果:", result)
    except asyncio.TimeoutError:
        print("超时，已等待:", round(time.perf_counter() - start, 2), "秒")

asyncio.run(main())


async def main():
    task = asyncio.create_task(slow_task(2.0))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("任务已取消，cancelled:", task.cancelled())

asyncio.run(main())


async def ok(item):
    await asyncio.sleep(0.05)
    return f"ok-{item}"

async def fail(item):
    await asyncio.sleep(0.05)
    raise ValueError(f"坏任务-{item}")

async def main():
    results = await asyncio.gather(ok(1), fail(2), ok(3), return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            print("失败:", type(result).__name__, result)
        else:
            print("成功:", result)

asyncio.run(main())

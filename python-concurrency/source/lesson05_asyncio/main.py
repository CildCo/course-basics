import asyncio
import time

async def greet(name, delay):
    print("开始", name)
    await asyncio.sleep(delay)
    print("结束", name)
    return f"hello {name}"

async def main():
    result = await greet("码袋子", 0.2)
    print(result)

asyncio.run(main())


async def main():
    start = time.perf_counter()
    task_a = asyncio.create_task(greet("A", 0.3))
    task_b = asyncio.create_task(greet("B", 0.1))
    results = await asyncio.gather(task_a, task_b)
    print("结果:", results)
    print("总耗时:", round(time.perf_counter() - start, 2), "秒")

asyncio.run(main())


async def main():
    loop = asyncio.get_running_loop()
    print("事件循环:", type(loop).__name__)
    print("当前时间:", round(loop.time(), 2))
    await asyncio.sleep(0.05)
    print("等待后时间:", round(loop.time(), 2))

asyncio.run(main())

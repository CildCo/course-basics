import asyncio
import time
from collections import Counter

ITEMS = list(range(1, 31))

async def fetch(item, attempt=1):
    await asyncio.sleep(0.03)
    if item % 11 == 0:
        raise RuntimeError("永久失败")
    if item % 5 == 0 and attempt == 1:
        raise RuntimeError("首次失败")
    return item * 10


async def process(item, semaphore, stats):
    async with semaphore:
        stats["active"] += 1
        stats["max_active"] = max(stats["max_active"], stats["active"])
        try:
            for attempt in range(1, 4):
                try:
                    value = await fetch(item, attempt)
                    if attempt > 1:
                        stats["retries"] += 1
                    stats["success"].append(value)
                    return value
                except Exception as exc:
                    if attempt == 3:
                        stats["failed"].append((item, str(exc)))
                        return None
                    stats["retries"] += 1
                    await asyncio.sleep(0.01)
        finally:
            stats["active"] -= 1


async def main():
    global stats
    semaphore = asyncio.Semaphore(3)
    stats = {"success": [], "failed": [], "retries": 0, "active": 0, "max_active": 0}
    start = time.perf_counter()
    await asyncio.gather(*(process(item, semaphore, stats) for item in ITEMS))
    elapsed = time.perf_counter() - start

    print("成功:", len(stats["success"]))
    print("失败:", len(stats["failed"]), stats["failed"])
    print("重试次数:", stats["retries"])
    print("最大并发:", stats["max_active"])
    print("总耗时:", round(elapsed, 2), "秒")
    print("成功率:", f"{len(stats['success']) / len(ITEMS):.0%}")

asyncio.run(main())


print("成功结果数量:", len(stats["success"]))
print("失败任务编号:", [item for item, _ in stats["failed"]])
print("成功结果前 10 个:", sorted(stats["success"])[:10])

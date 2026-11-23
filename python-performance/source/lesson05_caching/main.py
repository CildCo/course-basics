import time
import tracemalloc
from functools import lru_cache

def fib_slow(n):
    if n < 2:
        return n
    return fib_slow(n - 1) + fib_slow(n - 2)

@lru_cache(maxsize=None)
def fib_cached(n):
    if n < 2:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)

start = time.perf_counter()
slow_value = fib_slow(30)
slow_seconds = time.perf_counter() - start

fib_cached.cache_clear()
start = time.perf_counter()
cached_value = fib_cached(30)
cached_seconds = time.perf_counter() - start

print("结果一致:", slow_value == cached_value)
print("朴素递归:", round(slow_seconds * 1000, 1), "毫秒")
print("缓存递归:", round(cached_seconds * 1000, 3), "毫秒")
print("倍数:", round(slow_seconds / cached_seconds, 1), "倍")


fib_cached.cache_clear()
_ = fib_cached(30)
first = fib_cached.cache_info()

_ = fib_cached(30)
second = fib_cached.cache_info()

print("首次:", first)
print("再次:", second)
total = second.hits + second.misses
print("命中率:", f"{second.hits / total:.1%}")


def squares_list(n):
    return [value * value for value in range(n)]

def squares_generator(n):
    return (value * value for value in range(n))

SIZE = 200_000
tracemalloc.start()

data = squares_list(SIZE)
list_current, list_peak = tracemalloc.get_traced_memory()
del data

tracemalloc.reset_peak()
total = sum(squares_generator(SIZE))
gen_current, gen_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print("列表峰值:", round(list_peak / 1024 / 1024, 2), "MB")
print("生成器峰值:", round(gen_peak / 1024, 1), "KB")
print("内存倍数:", round(list_peak / max(gen_peak, 1), 1), "倍")
print("生成器求和:", total)


import itertools

pipeline = (value * value for value in range(1_000_000) if value % 3 == 0)
first_values = list(itertools.islice(pipeline, 5))
print("前 5 个:", first_values)
print("剩余生成器:", pipeline)
pipeline.close()

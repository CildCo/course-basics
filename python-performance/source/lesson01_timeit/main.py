import timeit

def squares_loop(n):
    result = []
    for value in range(n):
        result.append(value * value)
    return result

def squares_comp(n):
    return [value * value for value in range(n)]

print("结果一致:", squares_loop(10) == squares_comp(10))


REPEAT = 5
NUMBER = 200

loop_times = timeit.repeat(lambda: squares_loop(2000), repeat=REPEAT, number=NUMBER)
comp_times = timeit.repeat(lambda: squares_comp(2000), repeat=REPEAT, number=NUMBER)

print("for 循环每次:", [round(t / NUMBER * 1e6, 1) for t in loop_times], "微秒")
print("列表推导每次:", [round(t / NUMBER * 1e6, 1) for t in comp_times], "微秒")
print("最快样本倍数:", round(min(loop_times) / min(comp_times), 2), "倍")


import time

def build_index(rows):
    index = {}
    for key, value in rows:
        index[key] = value
    return index

rows = [(f"key-{i % 500}", i) for i in range(20000)]

times = []
for _ in range(6):
    start = time.perf_counter()
    build_index(rows)
    times.append(time.perf_counter() - start)

print("每轮耗时(毫秒):", [round(t * 1000, 2) for t in times])
print("首轮 / 最快:", round(times[0] / min(times), 2), "倍")


for number in (1, 100, 1000):
    best = min(timeit.repeat(lambda: squares_comp(2000), repeat=3, number=number))
    print(f"number={number:4d}  单次 {best / number * 1e6:7.1f} 微秒")

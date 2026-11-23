calls = 0

def fib_naive(n):
    global calls
    calls += 1
    if n < 2:
        return n
    return fib_naive(n - 1) + fib_naive(n - 2)

calls = 0
result = fib_naive(10)
print("fib(10) =", result)
print("朴素递归调用次数:", calls)


from functools import lru_cache

calls = 0

@lru_cache(maxsize=None)
def fib_memo(n):
    global calls
    calls += 1
    if n < 2:
        return n
    return fib_memo(n - 1) + fib_memo(n - 2)

calls = 0
result = fib_memo(10)
print("fib(10) =", result)
print("记忆化调用次数:", calls)
print("缓存信息:", fib_memo.cache_info())


def fib_table(n):
    if n < 2:
        return [0, 1][: n + 1]
    table = [0] * (n + 1)
    table[1] = 1
    for index in range(2, n + 1):
        table[index] = table[index - 1] + table[index - 2]
    return table

table = fib_table(10)
print("状态表:", table)
print("fib(10) =", table[10])


def climb_stairs(n):
    if n <= 2:
        return n
    first, second = 1, 2
    for _ in range(3, n + 1):
        first, second = second, first + second
    return second

for n in range(1, 11):
    print(f"{n} 级台阶: {climb_stairs(n)} 种走法")

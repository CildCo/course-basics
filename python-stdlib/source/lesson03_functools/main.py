from functools import partial

def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
cube = partial(power, exponent=3)
print("5 的平方：", square(5))
print("2 的立方：", cube(2))
print("原函数：", square.func.__name__)
print("预设参数：", square.keywords)


from functools import lru_cache

calls = 0

@lru_cache(maxsize=None)
def fib(n):
    global calls
    calls += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print("fib(20) =", fib(20))
print("实际计算次数：", calls)
print("缓存信息：", fib.cache_info())


from functools import reduce

numbers = [1, 2, 3, 4, 5]
print("累乘：", reduce(lambda a, b: a * b, numbers))
print("拼接：", reduce(lambda a, b: a + b, ["py", "thon", "!"], ""))


from functools import wraps

def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("调用", func.__name__)
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a, b):
    """返回两个数之和。"""
    return a + b

print("结果：", add(2, 3))
print("函数名：", add.__name__)
print("文档：", add.__doc__)

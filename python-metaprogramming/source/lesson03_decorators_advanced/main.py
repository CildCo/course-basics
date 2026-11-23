import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import functools


def trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"-> {func.__name__}{args}")
        result = func(*args, **kwargs)
        print(f"<- {func.__name__} = {result}")
        return result

    return wrapper


@trace
def add(a, b):
    "返回两个数之和"
    return a + b


print("结果:", add(2, 3))
print("名称:", add.__name__)
print("文档:", add.__doc__)


def retry(times=3, exceptions=(ValueError,)):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    print(f"第 {attempt} 次失败: {exc}")
                    if attempt == times:
                        raise

        return wrapper

    return decorate


state = {"calls": 0}


@retry(times=3, exceptions=(ValueError,))
def unstable():
    state["calls"] += 1
    if state["calls"] < 3:
        raise ValueError("临时故障")
    return "成功"


print("最终结果:", unstable())
print("实际调用次数:", state["calls"])


class Counted:
    def __init__(self, func):
        self.func = func
        self.calls = 0
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.func(*args, **kwargs)


@Counted
def square(n):
    "返回平方"
    return n * n


print("结果:", square(4))
print("调用次数:", square.calls)
print("名称:", square.__name__)
print("文档:", square.__doc__)


def add_summary(cls):
    def summary(self):
        return f"{cls.__name__}(value={self.value})"

    cls.summary = summary
    return cls


@add_summary
class Box:
    "一个带数值的盒子"

    def __init__(self, value):
        self.value = value


print(Box(7).summary())
print(Box.__doc__)
print("summary 在类上:", "summary" in Box.__dict__)


from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
report = out / "03-decorator-report.txt"
report.write_text(
    "装饰器检查\n"
    "1. functools.wraps 保留函数元信息\n"
    "2. 带参数装饰器是三层函数\n"
    "3. 类装饰器适合批量补充类行为\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

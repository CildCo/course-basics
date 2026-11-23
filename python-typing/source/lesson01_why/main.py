def greet(name: str, times: int = 1) -> str:
    return (f"你好，{name}！") * times

print(greet("小明", 2))
print(greet(123))


print(greet.__annotations__)
print("参数注解：", greet.__annotations__["name"])
print("返回注解：", greet.__annotations__["return"])


class Lesson:
    def __init__(self, title: str) -> None:
        self.title = title

def describe(lesson: "Lesson") -> str:
    return "课程：" + lesson.title

print(describe.__annotations__)
print("直接调用：", describe(Lesson("类型注解")))


import inspect
from typing import get_type_hints

print("解析后：", get_type_hints(describe))
print("签名：", inspect.signature(greet))

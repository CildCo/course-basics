import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dataclasses import dataclass, field, fields
import inspect


@dataclass
class Point:
    x: int
    y: int = 0
    tags: list[str] = field(default_factory=list)


p = Point(3, 4)
print("对象:", p)
print("相等:", p == Point(3, 4))
print("签名:", inspect.signature(Point))
print("字段:", [item.name for item in fields(Point)])
print("y 默认值:", fields(Point)[1].default)
print("tags 工厂:", fields(Point)[2].default_factory.__name__)
print("默认列表不共享:", Point(1).tags is Point(2).tags)


print("__init__:", Point.__init__.__qualname__)
print("__repr__:", Point.__repr__.__qualname__)
print("__eq__:", Point.__eq__.__qualname__)
print("实例字典:", p.__dict__)


try:
    @dataclass
    class Broken:
        x: int = 0
        y: int
except TypeError as exc:
    print("默认值顺序:", exc)


def mini_dataclass(cls):
    names = list(cls.__annotations__)

    def __init__(self, *args, **kwargs):
        if len(args) > len(names):
            raise TypeError("参数过多")
        for name, value in zip(names, args):
            setattr(self, name, value)
        for name in names[len(args):]:
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
            elif hasattr(cls, name):
                setattr(self, name, getattr(cls, name))
            else:
                raise TypeError(f"缺少参数: {name}")
        if kwargs:
            raise TypeError(f"未知参数: {sorted(kwargs)}")

    def __repr__(self):
        body = ", ".join(f"{name}={getattr(self, name)!r}" for name in names)
        return f"{type(self).__name__}({body})"

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return all(getattr(self, name) == getattr(other, name) for name in names)

    cls.__init__ = __init__
    cls.__repr__ = __repr__
    cls.__eq__ = __eq__
    return cls


@mini_dataclass
class User:
    name: str
    age: int = 18


u = User("Ada")
print(u)
print("相等:", u == User("Ada", 18))
print("__init__ 来源:", User.__init__.__qualname__)
try:
    User()
except TypeError as exc:
    print("缺少字段:", exc)


from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
report = out / "05-dataclass-report.txt"
report.write_text(
    "dataclass 检查\n"
    "1. 装饰器读取类型注解并生成方法\n"
    "2. 可变默认值要用 default_factory\n"
    "3. 有默认值的字段不能排在无默认值字段前\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

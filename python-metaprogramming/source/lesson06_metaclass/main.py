import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class Plain:
    pass


print("类的类型:", type(Plain))
print("实例的类型:", type(Plain()))
print("type 的类型:", type(type))

Dynamic = type("Dynamic", (object,), {"kind": "generated"})
print("动态类:", Dynamic)
print("类属性:", Dynamic.kind)


class Base:
    registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        name = getattr(cls, "name", "")
        if name:
            Base.registry[name] = cls


class Json(Base):
    name = "json"


class Csv(Base):
    name = "csv"


print("注册表:", Base.registry)
print("按名字取类:", Base.registry["json"].__name__)
print("是 Base 的子类:", issubclass(Json, Base))


class RequireName(type):
    def __new__(mcls, name, bases, namespace):
        if name != "PluginBase" and not namespace.get("name"):
            raise TypeError(f"{name} 缺少 name")
        cls = super().__new__(mcls, name, bases, namespace)
        cls.kind = "plugin"
        return cls


class PluginBase(metaclass=RequireName):
    pass


class Ping(PluginBase):
    name = "ping"


print("PluginBase 的元类:", type(PluginBase).__name__)
print("Ping 的元类:", type(Ping).__name__)
print("Ping.kind:", Ping.kind)
try:
    class Broken(PluginBase):
        pass
except TypeError as exc:
    print("Broken:", exc)


from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
report = out / "06-metaclass-report.txt"
report.write_text(
    "元类检查\n"
    "1. 类对象默认由 type 创建\n"
    "2. __init_subclass__ 适合子类登记\n"
    "3. 元类适合在类创建前校验或改写命名空间\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

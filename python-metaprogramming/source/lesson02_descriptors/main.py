import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class PositiveInt:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.private_name)

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError(f"{self.public_name} 必须是 int")
        if value <= 0:
            raise ValueError(f"{self.public_name} 必须大于 0")
        setattr(instance, self.private_name, value)


class Product:
    price = PositiveInt()
    stock = PositiveInt()

    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

    def __repr__(self):
        return f"Product({self.name!r}, price={self.price}, stock={self.stock})"


p = Product("键盘", 299, 12)
print(p)
print("类属性:", type(Product.price).__name__)
print("实例读取:", p.price, p.stock)
for field, value in [("price", -1), ("stock", "3")]:
    try:
        setattr(p, field, value)
    except Exception as exc:
        print(f"{field} -> {type(exc).__name__}: {exc}")


class NonData:
    def __get__(self, instance, owner=None):
        print("[non-data] __get__")
        return "from non-data"


class Data:
    def __get__(self, instance, owner=None):
        print("[data] __get__")
        return "from data"

    def __set__(self, instance, value):
        print("[data] __set__")


class Demo:
    a = NonData()
    b = Data()


d = Demo()
d.__dict__["a"] = "instance a"
d.__dict__["b"] = "instance b"
print("a =", d.a)
print("b =", d.b)


class Greeter:
    def hello(self):
        return "hello"


g = Greeter()
print("类访问:", type(Greeter.hello).__name__)
print("实例访问:", type(g.hello).__name__)
print("绑定到实例:", g.hello.__self__ is g)
print("调用结果:", g.hello())


from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
report = out / "02-descriptor-report.txt"
report.write_text(
    "描述符检查\n"
    "1. __set_name__ 在类创建时绑定属性名\n"
    "2. 数据描述符优先于实例字典\n"
    "3. 函数通过 __get__ 绑定实例，成为方法\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

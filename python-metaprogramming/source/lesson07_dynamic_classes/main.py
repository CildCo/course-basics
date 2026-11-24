import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import types


def init(self, value):
    self.value = value


Dynamic = type(
    "DynamicBox",
    (),
    {
        "__init__": init,
        "double": lambda self: self.value * 2,
        "kind": "dynamic",
    },
)
d = Dynamic(21)
print(type(d).__name__, d.value, d.double(), d.kind)


def body(namespace):
    namespace["__init__"] = init
    namespace["kind"] = "new_class"


Smart = types.new_class("SmartBox", (), exec_body=body)
s = Smart(5)
print(type(s).__name__, s.value, s.kind)


import json


class Registry:
    def __init__(self):
        self.items = {}

    def register(self, name):
        def decorate(cls):
            if name in self.items:
                raise ValueError(f"重复注册: {name}")
            self.items[name] = cls
            cls.registry_name = name
            return cls

        return decorate

    def create(self, name, **options):
        try:
            cls = self.items[name]
        except KeyError as exc:
            raise KeyError(f"未注册: {name}") from exc
        return cls(**options)

    def names(self):
        return sorted(self.items)


serializers = Registry()


@serializers.register("json")
class JsonSerializer:
    def __init__(self, indent=2):
        self.indent = indent

    def encode(self, data):
        return json.dumps(data, ensure_ascii=False, indent=self.indent)


@serializers.register("csv")
class CsvSerializer:
    def __init__(self, delimiter=","):
        self.delimiter = delimiter

    def encode(self, rows):
        return "\n".join(self.delimiter.join(str(cell) for cell in row) for row in rows)


print("已注册:", serializers.names())
print("JSON:", serializers.create("json", indent=None).encode({"name": "示例课程"}))
print("CSV:")
print(serializers.create("csv").encode([["name", "score"], ["Ada", 95]]))


try:
    @serializers.register("json")
    class Duplicate:
        pass
except ValueError as exc:
    print("重复:", exc)

try:
    serializers.create("xml")
except KeyError as exc:
    print("未知格式:", exc)

print("注册表未被污染:", serializers.names())


from pathlib import Path

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
report = out / "07-registry-report.txt"
report.write_text(
    "动态类与注册表检查\n"
    "1. type() 和 types.new_class() 可在运行时建类\n"
    "2. 注册表保存名字到类的映射\n"
    "3. 重复名和未知名字都要显式报错\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

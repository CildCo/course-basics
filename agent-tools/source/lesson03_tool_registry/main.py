import ast
import json
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

ORDERS = json.loads(data_path("orders.json").read_text(encoding="utf-8"))["orders"]

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_calc(expression):
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](walk(node.operand))
        raise ValueError(f"不支持的表达式节点: {type(node).__name__}")

    return walk(ast.parse(expression, mode="eval"))


def query_orders(region, status="paid", limit=5):
    rows = [
        order
        for order in ORDERS
        if order["region"] == region and order["status"] == status
    ]
    rows.sort(key=lambda order: (-order["amount"], order["order_id"]))
    return rows[:limit]


@dataclass
class Tool:
    name: str
    permission: str
    handler: Callable[..., Any]


class Registry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        if tool.name in self.tools:
            raise ValueError(f"工具重复注册: {tool.name}")
        self.tools[tool.name] = tool

    def call(self, name, **kwargs):
        if name not in self.tools:
            raise KeyError(f"工具未注册: {name}")
        tool = self.tools[name]
        if tool.permission == "dangerous":
            raise PermissionError(f"工具 {name} 属于危险权限，默认不允许调用")
        return tool.handler(**kwargs)


print("示例订单:")
for order in query_orders("华东", limit=2):
    print(f"  {order['order_id']} {order['customer']} {order['amount']:.2f} 元")


OUTPUT_DIR = (Path.cwd() / "output").resolve()
OUTPUT_DIR.mkdir(exist_ok=True)
ALLOWED_SUFFIXES = {".md", ".txt", ".json", ".jsonl"}


def resolve_output(relative):
    path = Path(relative)
    if path.is_absolute():
        raise PermissionError("只接受 output/ 下的相对路径")
    target = (OUTPUT_DIR / path).resolve()
    if OUTPUT_DIR not in target.parents:
        raise PermissionError(f"路径越界: {relative}")
    if target.suffix not in ALLOWED_SUFFIXES:
        raise PermissionError(f"不允许的文件类型: {target.suffix}")
    return target


def write_report(path, content):
    target = resolve_output(path)
    target.write_text(content, encoding="utf-8", newline="\n")
    return {
        "path": target.relative_to(Path.cwd().resolve()).as_posix(),
        "bytes": len(content.encode("utf-8")),
    }


def delete_file(path):
    raise RuntimeError("危险操作不应被执行")


registry = Registry()
registry.register(Tool("calc", "safe", safe_calc))
registry.register(Tool("query_orders", "read", query_orders))
registry.register(Tool("write_report", "write", write_report))
registry.register(Tool("delete_file", "dangerous", delete_file))

print("已注册工具:")
for name, tool in sorted(registry.tools.items()):
    print(f"- {name:14s} permission={tool.permission}")


cases = [
    ("查询", "query_orders", {"region": "华东", "limit": 2}),
    ("未注册", "http_request", {"url": "https://example.com"}),
    ("危险工具", "delete_file", {"path": "orders.json"}),
    ("路径越界", "write_report", {"path": "../notes.md", "content": "x"}),
    ("危险后缀", "write_report", {"path": "notes.exe", "content": "x"}),
    ("合法写入", "write_report", {"path": "region-report.md", "content": "# 华东订单\n"}),
]

for label, name, args in cases:
    try:
        result = registry.call(name, **args)
        summary = result if not isinstance(result, list) else f"{len(result)} 条订单"
        print(f"{label}: 允许 -> {summary}")
    except (KeyError, PermissionError, ValueError) as exc:
        print(f"{label}: 拒绝 -> {type(exc).__name__}: {exc}")


target = Path.cwd() / "output" / "region-report.md"
print("本课写入:", target.name, target.stat().st_size, "字节")
print("内容:")
print(target.read_text(encoding="utf-8").strip())

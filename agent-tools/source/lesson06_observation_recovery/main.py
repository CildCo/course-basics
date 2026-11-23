import json
from dataclasses import dataclass
from pathlib import Path


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


class InvalidArgs(ValueError):
    pass


class TransientError(RuntimeError):
    pass


class BusinessError(ValueError):
    pass


@dataclass
class Observation:
    step: int
    tool: str
    args: dict
    ok: bool
    value: object = None
    error_kind: str = ""
    error_message: str = ""


def classify(exc):
    if isinstance(exc, InvalidArgs):
        return "validation"
    if isinstance(exc, TransientError):
        return "transient"
    if isinstance(exc, PermissionError):
        return "permission"
    if isinstance(exc, BusinessError):
        return "business"
    return "internal"


print("观察字段:", list(Observation.__dataclass_fields__))


RECOVERY = {
    "validation": "修正参数后重试同一工具",
    "transient": "按退避重试，最多 3 次",
    "permission": "停止该步骤，向用户说明需要的权限",
    "business": "换备用方案或缩小任务范围",
    "internal": "停止循环，保留现场并报告",
}
for kind, action in RECOVERY.items():
    print(f"{kind:10s} -> {action}")


class OrderService:
    def __init__(self, orders):
        self.orders = orders
        self.query_calls = 0

    def query_orders(self, region, status="paid", limit=5):
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise InvalidArgs("limit 必须是整数")
        if region not in {"华东", "华北", "华南", "西南"}:
            raise BusinessError(f"没有匹配地区的订单: {region}")
        self.query_calls += 1
        if self.query_calls == 1:
            raise TransientError("查询服务临时超时")
        rows = [
            order
            for order in self.orders
            if order["region"] == region and order["status"] == status
        ]
        if not rows:
            raise BusinessError("没有符合条件的订单")
        rows.sort(key=lambda order: (-order["amount"], order["order_id"]))
        return rows[:limit]

    def write_report(self, path, content):
        if not path or Path(path).name != path:
            raise PermissionError("只允许写入 output/ 下的文件名")
        target = out / path
        target.write_text(content, encoding="utf-8", newline="\n")
        return {"path": path, "bytes": len(content.encode("utf-8"))}


def decide(observations):
    if not observations:
        return "query_orders", {"region": "华冬"}
    last = observations[-1]
    if last.error_kind == "business":
        return "query_orders", {"region": "华东", "limit": "五"}
    if last.error_kind == "validation":
        return "query_orders", {"region": "华东", "limit": 5}
    if last.error_kind == "transient":
        return "query_orders", {"region": "华东", "limit": 5}
    if last.ok and last.tool == "query_orders":
        return "write_report", {"path": "../summary.md", "content": f"订单数: {len(last.value)}"}
    if last.error_kind == "permission":
        count = len(observations[-2].value)
        return "write_report", {"path": "recovery.md", "content": f"订单数: {count}"}
    return "finish", {}


service = OrderService(ORDERS)
observations = []
for step in range(1, 9):
    tool, args = decide(observations)
    if tool == "finish":
        break
    try:
        value = getattr(service, tool)(**args)
    except Exception as exc:
        observations.append(
            Observation(step, tool, args, False, None, classify(exc), str(exc))
        )
    else:
        observations.append(Observation(step, tool, args, True, value, "", ""))

for item in observations:
    state = "成功" if item.ok else "失败"
    if item.ok and isinstance(item.value, list):
        detail = f"{len(item.value)} 条订单"
    elif item.ok:
        detail = f"{item.value['path']}（{item.value['bytes']} 字节）"
    else:
        detail = item.error_message
    print(f"{item.step} {item.tool:14s} {state} {item.error_kind:10s} {detail}")
print()
print("最终报告:")
print((out / "recovery.md").read_text(encoding="utf-8"))


from collections import Counter

failed = Counter(item.error_kind for item in observations if not item.ok)
print("失败类型统计:", dict(failed))
print("总步骤:", len(observations))
print("成功步骤:", sum(1 for item in observations if item.ok))
print("恢复是否完成:", (out / "recovery.md").exists())

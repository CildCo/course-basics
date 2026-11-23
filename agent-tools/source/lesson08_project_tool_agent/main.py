import hashlib
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
POLICY = json.loads(data_path("policy.json").read_text(encoding="utf-8"))
REGIONS = ["华东", "华北", "华南", "西南"]


class ToolTransientError(RuntimeError):
    """模拟可以重试的临时故障。"""


def query_orders(region, status="paid", limit=100):
    rows = [
        order
        for order in ORDERS
        if order["region"] == region and order["status"] == status
    ]
    rows.sort(key=lambda order: (-order["amount"], order["order_id"]))
    return rows[:limit]


def summarize_orders(orders):
    total = sum(order["amount"] for order in orders)
    return {
        "count": len(orders),
        "total": round(total, 2),
        "avg": round(total / len(orders), 2) if orders else 0.0,
    }


def top_orders(orders, n=3):
    rows = sorted(orders, key=lambda order: (-order["amount"], order["order_id"]))
    return [
        {"order_id": row["order_id"], "customer": row["customer"], "amount": row["amount"]}
        for row in rows[:n]
    ]


def compose_report(goal, summary, top):
    lines = [
        "# 订单分析报告",
        "",
        f"任务：{goal}",
        "",
        "## 汇总",
        f"- 订单数：{summary['count']}",
        f"- 总额：{summary['total']:.2f} 元",
        f"- 客单价：{summary['avg']:.2f} 元",
        "",
        "## 金额前三",
    ]
    for rank, item in enumerate(top, 1):
        lines.append(f"{rank}. {item['order_id']} {item['customer']} {item['amount']:.2f} 元")
    lines.extend(["", "## 说明", "本报告由本地工具生成，没有发起网络请求。"])
    return "\n".join(lines) + "\n"


def write_report(path, content):
    target = (out / path).resolve()
    if out.resolve() not in target.parents:
        raise PermissionError(f"路径越界: {path}")
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"path": path, "bytes": len(content.encode("utf-8"))}


class OrderService:
    def __init__(self):
        self.calls = 0

    def query_orders(self, region, status="paid", limit=100):
        self.calls += 1
        if self.calls == 1:
            raise ToolTransientError("第一次查询超时")
        return query_orders(region, status, limit)


service = OrderService()
TOOLS = {
    "query_orders": service.query_orders,
    "summarize_orders": summarize_orders,
    "top_orders": top_orders,
    "compose_report": compose_report,
    "write_report": write_report,
}
PERMISSIONS = {
    "query_orders": "read",
    "summarize_orders": "compute",
    "top_orders": "compute",
    "compose_report": "compute",
    "write_report": "write",
}
print("本地工具:", ", ".join(TOOLS))
print("样例:", summarize_orders(query_orders("华东")))


SPECS = {
    item["name"]: item
    for item in json.loads(data_path("tool_specs.json").read_text(encoding="utf-8"))["tools"]
}
SPECS["compose_report"] = {
    "parameters": {
        "type": "object",
        "properties": {
            "goal": {"type": "string"},
            "summary": {"type": "object"},
            "top": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["goal", "summary", "top"],
        "additionalProperties": False,
    }
}

TYPE_CHECKS = {
    "object": lambda item: isinstance(item, dict),
    "array": lambda item: isinstance(item, list),
    "string": lambda item: isinstance(item, str),
    "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
    "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
    "boolean": lambda item: isinstance(item, bool),
}


def validate_value(value, schema, path="$"):
    errors = []
    expected = schema.get("type")
    if expected and not TYPE_CHECKS[expected](value):
        return [f"{path}: 期望 {expected}，实际是 {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: 必须是 {schema['enum']} 之一")
    if expected in {"integer", "number"}:
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: 不能小于 {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: 不能大于 {schema['maximum']}")
    if expected == "array":
        for index, item in enumerate(value):
            errors.extend(validate_value(item, schema.get("items", {}), f"{path}[{index}]"))
    if expected == "object":
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: 缺少必填参数")
        for key, item in value.items():
            if key not in properties:
                if schema.get("additionalProperties") is False:
                    errors.append(f"{path}.{key}: 不允许的参数")
                continue
            errors.extend(validate_value(item, properties[key], f"{path}.{key}"))
    return errors


def validate_args(tool, args):
    return validate_value(args, SPECS[tool]["parameters"])


print(validate_args("query_orders", {"region": "华东", "limit": 3}))
print(validate_args("write_report", {"path": "demo.md"}))


def plan(task):
    """确定性 Planner：识别地区和状态，生成固定结构的计划。"""
    region = next((item for item in REGIONS if item in task), None)
    if region is None:
        raise ValueError("任务里没有可识别的地区")
    status = "pending" if "待支付" in task else "paid"
    return {
        "goal": task,
        "steps": [
            {
                "id": "s1",
                "tool": "query_orders",
                "args": {"region": region, "status": status, "limit": 100},
                "depends_on": [],
            },
            {
                "id": "s2",
                "tool": "summarize_orders",
                "args": {"orders": "$s1"},
                "depends_on": ["s1"],
            },
            {
                "id": "s3",
                "tool": "top_orders",
                "args": {"orders": "$s1", "n": 3},
                "depends_on": ["s1"],
            },
            {
                "id": "s4",
                "tool": "compose_report",
                "args": {"goal": "$goal", "summary": "$s2", "top": "$s3"},
                "depends_on": ["s2", "s3"],
            },
            {
                "id": "s5",
                "tool": "write_report",
                "args": {"path": "agent-report.md", "content": "$s4"},
                "depends_on": ["s4"],
            },
        ],
    }


task = "分析华东地区已支付订单：给出订单数、总额、客单价和金额前三，并生成报告。"
plan_data = plan(task)
print("目标:", plan_data["goal"])
for step in plan_data["steps"]:
    deps = ",".join(step["depends_on"]) or "-"
    print(f"{step['id']} {step['tool']:16s} 依赖={deps}")


def canonical(entry):
    payload = {
        key: entry[key]
        for key in ("index", "tool", "args_hash", "decision", "reason", "result", "prev")
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def entry_hash(entry):
    return hashlib.sha256(canonical(entry).encode("utf-8")).hexdigest()


class Guardrail:
    def __init__(self, policy):
        self.policy = policy
        self.calls = 0
        self.write_bytes = 0
        self.clock = 0.0
        self.audit = []

    def check(self, tool, permission, args):
        if tool in self.policy["dangerous"]:
            return False, "危险操作，默认拒绝"
        if self.calls >= self.policy["budget"]["max_tool_calls"]:
            return False, "调用次数超出预算"
        if self.clock >= self.policy["budget"]["max_seconds"]:
            return False, "时间预算耗尽"
        if permission == "write":
            size = len(str(args.get("content", "")).encode("utf-8"))
            if self.write_bytes + size > self.policy["budget"]["max_write_bytes"]:
                return False, "写入字节数超出预算"
        return True, "允许"

    def wait(self, seconds):
        self.clock = round(self.clock + seconds, 2)

    def record(self, tool, args, allowed, reason, result):
        args_hash = hashlib.sha256(
            json.dumps(args, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        entry = {
            "index": len(self.audit),
            "tool": tool,
            "args_hash": args_hash[:12],
            "decision": "allow" if allowed else "deny",
            "reason": reason,
            "result": str(result)[:120],
            "prev": self.audit[-1]["hash"] if self.audit else "0" * 64,
        }
        entry["hash"] = entry_hash(entry)
        self.audit.append(entry)
        return entry


def verify_audit(entries):
    prev = "0" * 64
    for entry in entries:
        if entry["prev"] != prev or entry_hash(entry) != entry["hash"]:
            return False
        prev = entry["hash"]
    return True


print("护栏配置:", POLICY["budget"])


@dataclass
class Observation:
    step: int
    step_id: str
    tool: str
    ok: bool
    value: object = None
    error_kind: str = ""
    message: str = ""


def bind_args(args, results, context):
    bound = {}
    for key, value in args.items():
        if isinstance(value, str) and value.startswith("$"):
            ref = value[1:]
            bound[key] = context["goal"] if ref == "goal" else results[ref]
        else:
            bound[key] = value
    return bound


def order_steps(steps):
    remaining = {step["id"]: step for step in steps}
    done = set()
    order = []
    while remaining:
        ready = [
            step_id
            for step_id, step in remaining.items()
            if all(dep in done for dep in step["depends_on"])
        ]
        if not ready:
            raise ValueError("计划有循环依赖或缺少依赖")
        for step_id in sorted(ready):
            order.append(remaining.pop(step_id))
            done.add(step_id)
    return order


def brief(value):
    if isinstance(value, list):
        return f"{len(value)} 条"
    if isinstance(value, dict):
        if "total" in value:
            return f"总额 {value['total']:.2f}"
        if "bytes" in value:
            return f"{value['bytes']} 字节"
        return json.dumps(value, ensure_ascii=False)[:60]
    text = str(value).replace("\n", " ")
    return text[:60] + ("..." if len(text) > 60 else "")


def execute(plan_data, tools, guard):
    results = {}
    context = {"goal": plan_data["goal"]}
    observations = []
    rows = []
    stopped = False

    for step in order_steps(plan_data["steps"]):
        if stopped:
            rows.append({"id": step["id"], "tool": step["tool"], "status": "跳过", "detail": "上游失败"})
            continue

        call_args = bind_args(step["args"], results, context)
        errors = validate_args(step["tool"], call_args)
        if errors:
            message = "；".join(errors)
            observations.append(
                Observation(len(observations) + 1, step["id"], step["tool"], False, None, "validation", message)
            )
            rows.append({"id": step["id"], "tool": step["tool"], "status": "失败", "detail": message})
            stopped = True
            continue

        permission = PERMISSIONS[step["tool"]]
        success = False
        for attempt in range(1, 4):
            allowed, reason = guard.check(step["tool"], permission, call_args)
            if not allowed:
                guard.record(step["tool"], call_args, False, reason, "未执行")
                message = f"护栏拒绝: {reason}"
                observations.append(
                    Observation(len(observations) + 1, step["id"], step["tool"], False, None, "guard", message)
                )
                rows.append({"id": step["id"], "tool": step["tool"], "status": "失败", "detail": message})
                stopped = True
                break
            try:
                value = tools[step["tool"]](**call_args)
            except ToolTransientError as exc:
                guard.calls += 1
                guard.record(step["tool"], call_args, True, f"临时失败（第{attempt}次）", str(exc))
                observations.append(
                    Observation(
                        len(observations) + 1,
                        step["id"],
                        step["tool"],
                        False,
                        None,
                        "transient",
                        f"第 {attempt} 次: {exc}",
                    )
                )
                if attempt == 3:
                    rows.append({"id": step["id"], "tool": step["tool"], "status": "失败", "detail": "重试 3 次仍失败"})
                    stopped = True
                    break
                guard.wait(2 ** (attempt - 1))
            except Exception as exc:
                guard.calls += 1
                guard.record(step["tool"], call_args, True, "执行失败", str(exc))
                observations.append(
                    Observation(len(observations) + 1, step["id"], step["tool"], False, None, "internal", str(exc))
                )
                rows.append({"id": step["id"], "tool": step["tool"], "status": "失败", "detail": str(exc)})
                stopped = True
                break
            else:
                guard.calls += 1
                if permission == "write":
                    guard.write_bytes += len(str(call_args.get("content", "")).encode("utf-8"))
                guard.record(step["tool"], call_args, True, "成功", value)
                results[step["id"]] = value
                observations.append(
                    Observation(len(observations) + 1, step["id"], step["tool"], True, value, "", "")
                )
                rows.append({"id": step["id"], "tool": step["tool"], "status": "完成", "detail": brief(value)})
                success = True
                break

        if not success and not stopped:
            stopped = True

    return results, observations, rows


guard = Guardrail(POLICY)
results, observations, rows = execute(plan_data, TOOLS, guard)
print("执行结果:")
for row in rows:
    print(f"{row['id']} {row['tool']:16s} {row['status']:4s} {row['detail']}")
print()
print("观察条数:", len(observations))
for item in observations:
    if item.error_kind:
        print(f"  第 {item.step} 步 {item.step_id} {item.error_kind}: {item.message}")
print("工具调用:", guard.calls, "写入字节:", guard.write_bytes)


report = results["s5"]
print("报告文件:", report)
print()
print((out / "agent-report.md").read_text(encoding="utf-8"))
print("审计条数:", len(guard.audit))
print("审计链校验:", verify_audit(guard.audit))

audit_path = out / "agent-audit.jsonl"
audit_path.write_text(
    "\n".join(json.dumps(item, ensure_ascii=False) for item in guard.audit) + "\n",
    encoding="utf-8",
    newline="\n",
)
print("审计文件字节:", audit_path.stat().st_size)


import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

totals = {
    region: sum(
        order["amount"]
        for order in ORDERS
        if order["region"] == region and order["status"] == "paid"
    )
    for region in REGIONS
}

fig, ax = plt.subplots(figsize=(7.6, 4.0))
bars = ax.bar(list(totals.keys()), list(totals.values()), color="#4f81bd", width=0.55)
for bar, value in zip(bars, totals.values()):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 80, f"{value:,.2f}", ha="center", fontsize=9)
ax.set_ylabel("已支付金额（元）")
ax.set_title("各地区已支付订单总额")
fig.savefig(out / "region-totals.png", dpi=130, bbox_inches="tight")
plt.close(fig)
print("图片已写入:", (out / "region-totals.png").relative_to(Path.cwd()).as_posix())
display(Image(filename=str(out / "region-totals.png")))

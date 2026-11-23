import hashlib
import json
from collections import Counter
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

POLICY = json.loads(data_path("policy.json").read_text(encoding="utf-8"))
ORDERS = json.loads(data_path("orders.json").read_text(encoding="utf-8"))["orders"]
print("预算:", POLICY["budget"])
print("危险工具:", POLICY["dangerous"])


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


print("护栏已就绪")


def query_orders(region, status="paid", limit=5):
    rows = [
        order
        for order in ORDERS
        if order["region"] == region and order["status"] == status
    ]
    rows.sort(key=lambda order: (-order["amount"], order["order_id"]))
    return rows[:limit]


def write_report(path, content):
    target = out / path
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"path": path, "bytes": len(content.encode("utf-8"))}


TOOLS = {"query_orders": query_orders, "write_report": write_report}
PERMISSIONS = {
    "query_orders": "read",
    "write_report": "write",
    "delete_file": "dangerous",
    "http_request": "dangerous",
}


def guarded_call(guard, name, args):
    permission = PERMISSIONS.get(name, "dangerous")
    allowed, reason = guard.check(name, permission, args)
    result = None
    if allowed:
        result = TOOLS[name](**args)
        guard.calls += 1
        if permission == "write":
            guard.write_bytes += len(str(args.get("content", "")).encode("utf-8"))
    guard.record(name, args, allowed, reason, result)
    return allowed, reason, result


guard = Guardrail(POLICY)
scenarios = [
    ("查询华东订单", "query_orders", {"region": "华东", "limit": 2}),
    ("写小报告", "write_report", {"path": "guard-small.md", "content": "# 摘要\n"}),
    ("删除文件", "delete_file", {"path": "orders.json"}),
    ("写超预算报告", "write_report", {"path": "guard-big.md", "content": "A" * 5000}),
]
for label, name, args in scenarios:
    allowed, reason, result = guarded_call(guard, name, args)
    print(f"{label}: {'允许' if allowed else '拒绝'} - {reason}")

for index in range(1, 8):
    allowed, reason, result = guarded_call(guard, "query_orders", {"region": "华北", "limit": 1})
    print(f"批量查询 {index}: {'允许' if allowed else '拒绝'} - {reason}")


print("审计记录:")
for entry in guard.audit:
    print(
        f"{entry['index']:02d} {entry['tool']:14s} {entry['decision']:5s} "
        f"{entry['reason']:22s} args={entry['args_hash']} hash={entry['hash'][:8]}"
    )
print()
print("审计链校验:", verify_audit(guard.audit))
tampered = [dict(item) for item in guard.audit]
tampered[2]["decision"] = "allow"
print("篡改第 3 条后校验:", verify_audit(tampered))

audit_path = out / "audit.jsonl"
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

counts = Counter(entry["reason"] for entry in guard.audit)
labels = list(counts.keys())
values = list(counts.values())
colors = ["#4f81bd" if label == "允许" else "#c0504d" for label in labels]

fig, ax = plt.subplots(figsize=(8.2, 3.8))
bars = ax.barh(labels, values, color=colors)
for bar, value in zip(bars, values):
    ax.text(value + 0.1, bar.get_y() + bar.get_height() / 2, str(value), va="center", fontsize=9)
ax.set_xlabel("次数")
ax.set_title("护栏决策分布")
fig.savefig(out / "guardrail-decisions.png", dpi=130, bbox_inches="tight")
plt.close(fig)
print("图片已写入:", (out / "guardrail-decisions.png").relative_to(Path.cwd()).as_posix())
display(Image(filename=str(out / "guardrail-decisions.png")))

import json
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


def compose_report(summary, top):
    lines = [
        "# 华东已支付订单摘要",
        "",
        f"- 订单数：{summary['count']}",
        f"- 总额：{summary['total']:.2f} 元",
        f"- 客单价：{summary['avg']:.2f} 元",
        "",
        "## 金额前三",
    ]
    for rank, item in enumerate(top, 1):
        lines.append(f"{rank}. {item['order_id']} {item['customer']} {item['amount']:.2f} 元")
    return "\n".join(lines) + "\n"


def write_report(path, content):
    target = out / path
    target.write_text(content, encoding="utf-8", newline="\n")
    return {"path": path, "bytes": len(content.encode("utf-8"))}


TOOLS = {
    "query_orders": query_orders,
    "summarize_orders": summarize_orders,
    "top_orders": top_orders,
    "compose_report": compose_report,
    "write_report": write_report,
}

print("示例订单数:", len(query_orders("华东")))
print("汇总:", summarize_orders(query_orders("华东")))


def plan_task(task):
    """确定性规划器：从任务文本抽取地区、状态和条数。"""
    region = next((item for item in ["华东", "华北", "华南", "西南"] if item in task), "华东")
    status = "paid" if "已支付" in task else "pending"
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
                "args": {"summary": "$s2", "top": "$s3"},
                "depends_on": ["s2", "s3"],
            },
            {
                "id": "s5",
                "tool": "write_report",
                "args": {"path": "plan-report.md", "content": "$s4"},
                "depends_on": ["s4"],
            },
        ],
    }


task = "统计华东地区已支付订单总额，写出报告并列出金额最高的三笔"
plan = plan_task(task)
print("目标:", plan["goal"])
for step in plan["steps"]:
    deps = ",".join(step["depends_on"]) or "-"
    print(f"{step['id']}  {step['tool']:16s} 依赖={deps}")


def resolve_dependencies(steps):
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
            missing = sorted(
                {dep for step in remaining.values() for dep in step["depends_on"]} - done
            )
            raise ValueError(f"依赖无法满足: {missing}")
        for step_id in sorted(ready):
            order.append(remaining.pop(step_id))
            done.add(step_id)
    return order


def bind_args(args, results):
    bound = {}
    for key, value in args.items():
        if isinstance(value, str) and value.startswith("$"):
            bound[key] = results[value[1:]]
        else:
            bound[key] = value
    return bound


def execute_plan(plan, tools):
    results = {}
    rows = []
    for step in resolve_dependencies(plan["steps"]):
        call_args = bind_args(step["args"], results)
        try:
            value = tools[step["tool"]](**call_args)
        except Exception as exc:
            rows.append({"id": step["id"], "tool": step["tool"], "status": f"失败: {type(exc).__name__}: {exc}"})
            for rest in plan["steps"]:
                if rest["id"] not in results and rest["id"] != step["id"]:
                    rows.append({"id": rest["id"], "tool": rest["tool"], "status": "跳过"})
            break
        results[step["id"]] = value
        rows.append({"id": step["id"], "tool": step["tool"], "status": "完成"})
    return results, rows


results, rows = execute_plan(plan, TOOLS)
for row in rows:
    print(f"{row['id']} {row['tool']:16s} {row['status']}")
print()
print("摘要:", results["s2"])
print("前三:", [item["order_id"] for item in results["s3"]])
print("报告字节:", results["s5"]["bytes"])
print()
print((out / "plan-report.md").read_text(encoding="utf-8"))


bad_plan = {
    "steps": [
        {"id": "a", "tool": "query_orders", "args": {}, "depends_on": ["b"]},
        {"id": "b", "tool": "summarize_orders", "args": {"orders": "$a"}, "depends_on": ["a"]},
    ]
}
try:
    resolve_dependencies(bad_plan["steps"])
except ValueError as exc:
    print("依赖检查:", exc)

broken_plan = {
    "steps": [
        {
            "id": "x1",
            "tool": "query_orders",
            "args": {"region": "华东", "limit": 2},
            "depends_on": [],
        },
        {"id": "x2", "tool": "missing_tool", "args": {}, "depends_on": ["x1"]},
        {
            "id": "x3",
            "tool": "write_report",
            "args": {"path": "should-not-exist.md", "content": "x"},
            "depends_on": ["x2"],
        },
    ]
}
results2, rows2 = execute_plan(broken_plan, TOOLS)
for row in rows2:
    print(f"{row['id']} {row['tool']:14s} {row['status']}")
print("越界步骤是否写了文件:", (out / "should-not-exist.md").exists())


import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from IPython.display import Image, display

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

positions = {
    "s1": (0.06, 0.50),
    "s2": (0.31, 0.72),
    "s3": (0.31, 0.28),
    "s4": (0.56, 0.50),
    "s5": (0.80, 0.50),
}
labels = {
    "s1": "查询订单\nquery_orders",
    "s2": "汇总\nsummarize_orders",
    "s3": "前三\ntop_orders",
    "s4": "组装报告\ncompose_report",
    "s5": "写文件\nwrite_report",
}
for step_id, (x, y) in positions.items():
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            0.14,
            0.14,
            boxstyle="round,pad=0.015",
            linewidth=1.2,
            edgecolor="#3b6ea5",
            facecolor="#eef4fb",
        )
    )
    ax.text(x + 0.07, y + 0.07, labels[step_id], ha="center", va="center", fontsize=9)

for left, right in [("s1", "s2"), ("s1", "s3"), ("s2", "s4"), ("s3", "s4"), ("s4", "s5")]:
    start_x, start_y = positions[left]
    end_x, end_y = positions[right]
    ax.annotate(
        "",
        xy=(end_x, end_y + 0.07),
        xytext=(start_x + 0.14, start_y + 0.07),
        arrowprops=dict(arrowstyle="->", color="#3b6ea5", lw=1.3),
    )

ax.set_title("执行计划的有向无环图", fontsize=13)
fig.savefig(out / "plan-dag.png", dpi=130, bbox_inches="tight")
plt.close(fig)
print("图片已写入:", (out / "plan-dag.png").relative_to(Path.cwd()).as_posix())
display(Image(filename=str(out / "plan-dag.png")))

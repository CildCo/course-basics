from pathlib import Path
import json


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

specs = json.loads(data_path("tool_specs.json").read_text(encoding="utf-8"))
print("工具清单:", len(specs["tools"]), "个")
for spec in specs["tools"]:
    print(f"- {spec['name']:16s} 权限={spec['permission']:10s} {spec['description']}")


import ast
import operator


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_calc(expression):
    """只允许数字、括号和四则运算。"""

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


TOOLS = {
    "calc": {"run": lambda expression: safe_calc(expression), "label": "四则计算"},
    "count_chars": {"run": lambda text: len(text), "label": "统计字符数"},
}

print("calc:", safe_calc("(12*8+4)/2"))
print("count_chars:", TOOLS["count_chars"]["run"]("工具层负责把计划变成可检查的动作"))


from dataclasses import dataclass, field


@dataclass
class State:
    task: str
    observations: list = field(default_factory=list)
    finished: bool = False
    answer: object = None


class ScriptedModel:
    """确定性决策器：按已经完成的工具选择下一步。"""

    def decide(self, state):
        used = {item["tool"] for item in state.observations}
        if "calc" not in used:
            return {
                "thought": "先把数值算出来",
                "tool": "calc",
                "args": {"expression": "(12*8+4)/2"},
            }
        if "count_chars" not in used:
            return {
                "thought": "再统计说明文字的长度",
                "tool": "count_chars",
                "args": {"text": "工具层负责把计划变成可检查的动作"},
            }
        number = state.observations[0]["result"]
        chars = state.observations[1]["result"]
        return {
            "thought": "两个结果都拿到了，可以收尾",
            "tool": "finish",
            "args": {"answer": f"计算结果是 {number:g}，说明文字共 {chars} 个字符"},
        }


def run_agent(task, model, tools, max_steps=5):
    state = State(task=task)
    trace = []
    while not state.finished and len(trace) < max_steps:
        decision = model.decide(state)
        record = {
            "step": len(trace) + 1,
            "thought": decision["thought"],
            "tool": decision["tool"],
            "args": decision["args"],
        }
        if decision["tool"] == "finish":
            state.finished = True
            state.answer = decision["args"]["answer"]
            record["result"] = state.answer
            trace.append(record)
            break
        try:
            result = tools[decision["tool"]]["run"](**decision["args"])
            record["result"] = result
            state.observations.append(
                {"tool": decision["tool"], "args": decision["args"], "result": result}
            )
        except Exception as exc:
            record["result"] = f"失败: {exc}"
        trace.append(record)
    return state, trace


state, trace = run_agent("算一个数并统计一句话", ScriptedModel(), TOOLS)
for row in trace:
    print(f"[{row['step']}] 想法: {row['thought']}")
    print(f"    动作: {row['tool']}({row['args']})")
    print(f"    观察: {row['result']}")
print()
print("结束:", state.finished)
print("回答:", state.answer)


import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from IPython.display import Image, display

fig, ax = plt.subplots(figsize=(8.5, 4.8))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

boxes = {
    "模型\n看状态做决策": (0.08, 0.66),
    "工具\n执行动作": (0.62, 0.66),
    "状态\n目标与观察": (0.62, 0.18),
    "循环\n决策→动作→观察": (0.08, 0.18),
}
for label, (x, y) in boxes.items():
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            0.30,
            0.16,
            boxstyle="round,pad=0.02",
            linewidth=1.2,
            edgecolor="#3b6ea5",
            facecolor="#eef4fb",
        )
    )
    ax.text(x + 0.15, y + 0.08, label, ha="center", va="center", fontsize=11)

arrows = [
    ((0.38, 0.74), (0.62, 0.74), "选择工具"),
    ((0.77, 0.66), (0.77, 0.34), "写回结果"),
    ((0.62, 0.26), (0.38, 0.26), "提供上下文"),
    ((0.23, 0.34), (0.23, 0.66), "继续下一步"),
]
for start, end, label in arrows:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="->", color="#3b6ea5", lw=1.4),
    )
    ax.text(
        (start[0] + end[0]) / 2,
        (start[1] + end[1]) / 2,
        label,
        ha="center",
        va="bottom",
        fontsize=9,
        color="#444444",
    )

ax.set_title("Agent 的四个组成部分与循环", fontsize=13)
fig.savefig(out / "agent-loop.png", dpi=130, bbox_inches="tight")
plt.close(fig)
print("图片已写入:", (out / "agent-loop.png").relative_to(Path.cwd()).as_posix())
display(Image(filename=str(out / "agent-loop.png")))

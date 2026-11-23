import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sys


class DictPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class SlotPoint:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y


d = DictPoint(1, 2)
s = SlotPoint(1, 2)
print("DictPoint 实例:", sys.getsizeof(d), "字节")
print("DictPoint __dict__:", sys.getsizeof(d.__dict__), "字节")
print("SlotPoint 实例:", sys.getsizeof(s), "字节")
print("SlotPoint 有 __dict__:", hasattr(s, "__dict__"))
print("两者总占用:", sys.getsizeof(d) + sys.getsizeof(d.__dict__), sys.getsizeof(s))


from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from IPython.display import Image, display

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
dict_total = sys.getsizeof(d) + sys.getsizeof(d.__dict__)
slot_total = sys.getsizeof(s)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1, 1.35]})
ax = axes[0]
bars = ax.bar(
    ["instance + dict", "instance + slots"],
    [dict_total, slot_total],
    color=["#c97c7c", "#6f9fc0"],
    width=0.55,
)
for bar, value in zip(bars, [dict_total, slot_total]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 8,
        f"{value} B",
        ha="center",
        va="bottom",
        fontsize=10,
    )
ax.set_ylabel("bytes")
ax.set_title("Two-field object")
ax.set_ylim(0, max(dict_total, slot_total) * 1.22)
ax.spines[["top", "right"]].set_visible(False)

layout = axes[1]
layout.set_xlim(0, 10)
layout.set_ylim(0, 5)
layout.axis("off")
layout.add_patch(
    FancyBboxPatch(
        (0.4, 2.7),
        4.1,
        1.5,
        boxstyle="round,pad=0.06",
        facecolor="#f2d7d7",
        edgecolor="#8a5555",
        linewidth=1,
    )
)
layout.text(2.45, 3.45, "instance", ha="center", fontsize=10)
layout.text(2.45, 3.0, "__dict__ pointer", ha="center", fontsize=9)
layout.add_patch(
    FancyBboxPatch(
        (5.4, 1.5),
        4.0,
        2.6,
        boxstyle="round,pad=0.06",
        facecolor="#f7e7c6",
        edgecolor="#8a6d3b",
        linewidth=1,
    )
)
layout.text(7.4, 3.55, "external dict", ha="center", fontsize=10)
layout.text(7.4, 2.95, "x -> 1", ha="center", fontsize=9)
layout.text(7.4, 2.45, "y -> 2", ha="center", fontsize=9)
layout.text(7.4, 1.95, "extra keys", ha="center", fontsize=9)

layout.add_patch(
    FancyBboxPatch(
        (0.4, 0.2),
        4.1,
        1.4,
        boxstyle="round,pad=0.06",
        facecolor="#d8e7f1",
        edgecolor="#4d7690",
        linewidth=1,
    )
)
layout.text(2.45, 0.9, "slots instance", ha="center", fontsize=10)
layout.add_patch(
    FancyBboxPatch(
        (5.4, 0.2),
        4.0,
        1.4,
        boxstyle="round,pad=0.06",
        facecolor="#d8e7f1",
        edgecolor="#4d7690",
        linewidth=1,
    )
)
layout.text(7.4, 0.9, "x | y inline", ha="center", fontsize=10)
layout.annotate(
    "",
    xy=(5.3, 3.9),
    xytext=(4.6, 3.45),
    arrowprops=dict(arrowstyle="-|>", color="#8a5555", lw=1.2),
)
layout.set_title("Where fields live", fontsize=11)
fig.tight_layout()
image_path = out / "04-object-memory.png"
fig.savefig(image_path, dpi=140, bbox_inches="tight")
plt.close(fig)
display(Image(filename=str(image_path)))


try:
    s.z = 3
except AttributeError as exc:
    print("槽位外字段:", type(exc).__name__)


class SlotChild(SlotPoint):
    pass


class StrictChild(SlotPoint):
    __slots__ = ()


child = SlotChild(3, 4)
child.z = 5
print("普通子类重新获得 __dict__:", child.__dict__)

strict = StrictChild(6, 7)
try:
    strict.z = 8
except AttributeError as exc:
    print("严格子类:", type(exc).__name__)


import weakref


class NoWeak:
    __slots__ = ("x",)


class WithWeak:
    __slots__ = ("x", "__weakref__")


n = NoWeak()
n.x = 1
try:
    weakref.ref(n)
except TypeError as exc:
    print("NoWeak:", type(exc).__name__)

w = WithWeak()
w.x = 1
print("WithWeak 可弱引用:", weakref.ref(w)() is w)


report = out / "04-slots-report.txt"
report.write_text(
    f"对象内存检查\n普通实例加字典: {dict_total} 字节\n槽位实例: {slot_total} 字节\n"
    "结论: 字段固定且对象多时，槽位能减少每个实例的字典开销\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

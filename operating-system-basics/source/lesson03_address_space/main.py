from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

KB = 1024

segments = [
    {"name": "代码段 .text", "start": 0x0000, "size": 8 * KB, "perm": "r-x", "color": "#9DB4CE"},
    {"name": "只读数据 .rodata", "start": 0x2000, "size": 4 * KB, "perm": "r--", "color": "#B8C9DC"},
    {"name": "已初始化数据 .data", "start": 0x3000, "size": 4 * KB, "perm": "rw-", "color": "#F2C48D"},
    {"name": "未初始化数据 .bss", "start": 0x4000, "size": 4 * KB, "perm": "rw-", "color": "#F6D7B0"},
    {"name": "堆 heap", "start": 0x5000, "size": 24 * KB, "perm": "rw-", "color": "#8CC9A8"},
    {"name": "空闲区", "start": 0xB000, "size": 16 * KB, "perm": "---", "color": "#EEF1F5"},
    {"name": "栈 stack", "start": 0xF000, "size": 4 * KB, "perm": "rw-", "color": "#C9A7D4"},
]

print(f"{'段名':<18}{'起始':>8}{'结束':>10}{'大小':>8}  权限")
for segment in segments:
    end = segment["start"] + segment["size"]
    print(
        f"{segment['name']:<18}0x{segment['start']:04X}"
        f"  0x{end:04X}{segment['size'] // KB:>7} KB  {segment['perm']}"
    )


import matplotlib.pyplot as plt
from IPython.display import Image, display

fig, ax = plt.subplots(figsize=(8, 5.2))
for segment in segments:
    middle = segment["start"] + segment["size"] / 2
    ax.barh(middle, 1.5, height=segment["size"], left=0,
            color=segment["color"], edgecolor="white")
    ax.text(1.7, middle, f"{segment['name']}  {segment['perm']}",
            va="center", fontsize=10)

ax.set_xlim(0, 5.2)
ax.set_ylim(0, 0x10000)
ax.set_xticks([])
ax.set_yticks([segment["start"] + segment["size"] / 2 for segment in segments])
ax.set_yticklabels([f"0x{segment['start']:04X}" for segment in segments])
ax.set_ylabel("地址（低 → 高）")
ax.set_title("一个 64 KB 地址空间的典型布局")

ax.annotate("堆向高地址增长", xy=(0.75, 0xB000), xytext=(2.9, 0x9200),
            arrowprops=dict(arrowstyle="->", color="#555555"), fontsize=10)
ax.annotate("栈向低地址增长", xy=(0.75, 0xF800), xytext=(2.9, 0xE000),
            arrowprops=dict(arrowstyle="->", color="#555555"), fontsize=10)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.tight_layout()
figure_path = OUTPUT / "memory-layout.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
print("内存布局图已保存：", figure_path.relative_to(Path.cwd()).as_posix())


class BumpAllocator:
    def __init__(self, base, limit):
        self.base = base
        self.limit = limit
        self.cursor = base

    def allocate(self, size, label):
        if self.cursor + size > self.limit:
            raise MemoryError(f"{label} 需要 {size // KB} KB，堆空间不足")
        address = self.cursor
        self.cursor += size
        return address


heap = BumpAllocator(0x5000, 0x5000 + 24 * KB)
for label, size in [("列表", 3 * KB), ("字典", 5 * KB), ("缓存", 8 * KB)]:
    address = heap.allocate(size, label)
    print(f"{label:<4} 分配 {size // KB} KB，起始地址 0x{address:04X}")
print("堆指针停在：", hex(heap.cursor))

try:
    heap.allocate(12 * KB, "大对象")
except MemoryError as error:
    print("分配失败：", error)

stack_top = 0xF000
frame_size = 256
guard = 0xC000
depth = (stack_top - guard) // frame_size
print("每帧 256 字节时，最多可压入", depth, "层栈帧")
print("栈指针最低到：", hex(stack_top - depth * frame_size))


import sys

samples = {
    "小整数": 7,
    "字符串": "abc",
    "列表": [1, 2, 3],
    "字典": {"k": [4, 5]},
}

for label, value in samples.items():
    print(
        f"{label:<4} 类型 {type(value).__name__:<6}"
        f"id 0x{id(value):X} 占用 {sys.getsizeof(value)} 字节"
    )

print("提示：id 在不同运行中会变化，不能当作固定地址保存。")

import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

random.seed(42)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)


PAGE_SIZE = 4096
OFFSET_BITS = 12
OFFSET_MASK = PAGE_SIZE - 1


def split_address(address):
    return address >> OFFSET_BITS, address & OFFSET_MASK


for address in [0x0000, 0x1234, 0x7FFF, 0xF000]:
    page_number, offset = split_address(address)
    print(f"虚拟地址 0x{address:04X} -> 页号 {page_number}，页内偏移 0x{offset:03X}")

page_table = {0: 5, 1: 9, 2: 2, 3: 7}


def translate(address):
    page_number, offset = split_address(address)
    frame = page_table.get(page_number)
    if frame is None:
        return None
    return frame * PAGE_SIZE + offset


for address in [0x0123, 0x1450, 0x2ABC, 0x3FFF, 0x4000]:
    physical = translate(address)
    if physical is None:
        print(f"虚拟地址 0x{address:04X} 没有映射，触发缺页")
    else:
        print(f"虚拟地址 0x{address:04X} -> 物理地址 0x{physical:05X}")


trace = [0, 1, 2, 0, 3, 1, 0, 2, 3, 3, 0, 1]
frame_count = 3
frames = []
last_used = {}
faults = 0
snapshots = []

for step, page in enumerate(trace, 1):
    if page in frames:
        result = "命中"
        last_used[page] = step
    else:
        result = "缺页"
        faults += 1
        if len(frames) < frame_count:
            frames.append(page)
        else:
            victim = min(frames, key=lambda item: last_used[item])
            frames[frames.index(victim)] = page
        last_used[page] = step
    snapshots.append(list(frames))
    print(f"第 {step:>2} 次访问页 {page}：{result}，内存中的页 {frames}")

print("缺页次数：", faults)
print("缺页率：", f"{faults / len(trace):.0%}")


import matplotlib.pyplot as plt
from IPython.display import Image, display

palette = ["#4C78A8", "#F2A65A", "#6BBF8A", "#B07AA1", "#D65A5A"]
fig, ax = plt.subplots(figsize=(9.2, 3.4))

for step in range(len(trace)):
    for slot in range(frame_count):
        page = snapshots[step][slot] if slot < len(snapshots[step]) else None
        color = palette[page % len(palette)] if page is not None else "#EEF1F5"
        ax.add_patch(plt.Rectangle((step, slot), 0.92, 0.82,
                                   facecolor=color, edgecolor="white"))
        if page is not None:
            ax.text(step + 0.46, slot + 0.41, f"页 {page}",
                    ha="center", va="center", color="white", fontsize=9)

ax.set_xlim(0, len(trace))
ax.set_ylim(0, frame_count)
ax.set_xticks([index + 0.46 for index in range(len(trace))])
ax.set_xticklabels([str(index + 1) for index in range(len(trace))])
ax.set_yticks([index + 0.41 for index in range(frame_count)])
ax.set_yticklabels([f"帧 {index + 1}" for index in range(frame_count)])
ax.set_xlabel("访问序号")
ax.set_title(f"三帧 LRU 的页面变化（缺页 {faults} 次）")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.tight_layout()
figure_path = OUTPUT / "page-timeline.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
print("页面变化图已保存：", figure_path.relative_to(Path.cwd()).as_posix())


def fault_count(sequence, capacity):
    frames = []
    last_used = {}
    faults = 0
    for step, page in enumerate(sequence, 1):
        if page in frames:
            last_used[page] = step
        else:
            faults += 1
            if len(frames) < capacity:
                frames.append(page)
            else:
                victim = min(frames, key=lambda item: last_used[item])
                frames[frames.index(victim)] = page
            last_used[page] = step
    return faults


local_trace = [(index * 5) % 3 for index in range(120)]
random_trace = [random.randrange(0, 30) for _ in range(120)]

for label, sequence in [("局部性访问", local_trace), ("随机访问", random_trace)]:
    faults_in_run = fault_count(sequence, 3)
    hit_rate = 1 - faults_in_run / len(sequence)
    print(f"{label}: 访问 {len(sequence)} 次，缺页 {faults_in_run} 次，命中率 {hit_rate:.0%}")

import csv
import random
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

random.seed(7)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)


@dataclass
class Job:
    name: str
    arrival: int
    burst: int
    priority: int = 0


with data_path("workload.csv").open(encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

jobs = [
    Job(row["name"], int(row["arrival"]), int(row["burst"]), int(row["priority"]))
    for row in rows
]

print("作业数量：", len(jobs))
print("总运行时间：", sum(job.burst for job in jobs))
for job in jobs:
    print(f"{job.name} 到达 {job.arrival}，需要 {job.burst} 个时间单位，优先级 {job.priority}")


def run_fcfs(jobs):
    time_now = 0
    timeline = []
    for job in sorted(jobs, key=lambda item: (item.arrival, item.name)):
        start = max(time_now, job.arrival)
        end = start + job.burst
        timeline.append((job.name, start, end))
        time_now = end
    return timeline


def run_sjf(jobs):
    pending = sorted(jobs, key=lambda item: (item.arrival, item.burst, item.name))
    done = set()
    timeline = []
    time_now = 0
    while len(done) < len(jobs):
        ready = [
            job for job in pending
            if job.name not in done and job.arrival <= time_now
        ]
        if not ready:
            time_now = min(job.arrival for job in pending if job.name not in done)
            continue
        job = min(ready, key=lambda item: (item.burst, item.arrival, item.name))
        start = time_now
        end = start + job.burst
        timeline.append((job.name, start, end))
        done.add(job.name)
        time_now = end
    return timeline


def show(label, timeline, jobs):
    lookup = {job.name: job for job in jobs}
    rows = []
    print(label)
    for name, start, end in timeline:
        job = lookup[name]
        wait = start - job.arrival
        turnaround = end - job.arrival
        rows.append((wait, turnaround))
        print(f"  {name}: 开始 {start:>2}，结束 {end:>2}，等待 {wait:>2}，周转 {turnaround:>2}")
    average_wait = sum(row[0] for row in rows) / len(rows)
    average_turnaround = sum(row[1] for row in rows) / len(rows)
    print(f"  平均等待 {average_wait:.2f}，平均周转 {average_turnaround:.2f}")


fcfs_timeline = run_fcfs(jobs)
show("FCFS", fcfs_timeline, jobs)

sjf_timeline = run_sjf(jobs)
show("SJF（非抢占）", sjf_timeline, jobs)


def run_rr(jobs, quantum=2):
    pending = sorted(jobs, key=lambda item: (item.arrival, item.name))
    remaining = {job.name: job.burst for job in jobs}
    ready = deque()
    timeline = []
    finish = {}
    index = 0
    time_now = 0

    def admit(now):
        nonlocal index
        while index < len(pending) and pending[index].arrival <= now:
            ready.append(pending[index])
            index += 1

    admit(0)
    while len(finish) < len(jobs):
        if not ready:
            time_now = pending[index].arrival
            admit(time_now)
            continue
        job = ready.popleft()
        start = time_now
        slice_time = min(quantum, remaining[job.name])
        time_now += slice_time
        remaining[job.name] -= slice_time
        timeline.append((job.name, start, time_now))
        admit(time_now)
        if remaining[job.name] == 0:
            finish[job.name] = time_now
        else:
            ready.append(job)
    return timeline, finish


rr_timeline, rr_finish = run_rr(jobs, quantum=2)

print("时间片轮转，q=2")
for name, start, end in rr_timeline:
    print(f"  {start:>2}-{end:<2} {name}")

rows = []
for job in jobs:
    end = rr_finish[job.name]
    wait = end - job.arrival - job.burst
    turnaround = end - job.arrival
    rows.append((wait, turnaround))
    print(f"  {job.name}: 完成 {end:>2}，等待 {wait:>2}，周转 {turnaround:>2}")

average_wait = sum(row[0] for row in rows) / len(rows)
average_turnaround = sum(row[1] for row in rows) / len(rows)
print(f"  平均等待 {average_wait:.2f}，平均周转 {average_turnaround:.2f}")


import matplotlib.pyplot as plt
from IPython.display import Image, display

job_names = [job.name for job in jobs]
palette = ["#4C78A8", "#F2A65A", "#6BBF8A", "#B07AA1", "#D65A5A"]
colors = {name: palette[index % len(palette)] for index, name in enumerate(job_names)}

fig, axes = plt.subplots(3, 1, figsize=(10, 6.2), sharex=True)
charts = [
    ("FCFS", fcfs_timeline),
    ("SJF（非抢占）", sjf_timeline),
    ("时间片轮转 q=2", rr_timeline),
]

for ax, (label, timeline) in zip(axes, charts):
    for name, start, end in timeline:
        row = job_names.index(name)
        ax.barh(row, end - start, left=start, height=0.55,
                color=colors[name], edgecolor="white")
        ax.text((start + end) / 2, row, name, ha="center", va="center",
                color="white", fontsize=9)
    ax.set_yticks(range(len(job_names)))
    ax.set_yticklabels(job_names)
    ax.invert_yaxis()
    ax.set_title(label, loc="left", fontsize=11)
    ax.set_xlim(0, max(end for _, _, end in timeline) + 1)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)

axes[-1].set_xlabel("时间")
fig.suptitle("三种调度算法的执行顺序")
fig.tight_layout()
figure_path = OUTPUT / "scheduling-gantt.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
print("甘特图已保存：", figure_path.relative_to(Path.cwd()).as_posix())

import csv
import queue
import random
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

random.seed(11)


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
    priority: int
    remaining: int = 0
    start: int = -1
    finish: int = -1

    def __post_init__(self):
        self.remaining = self.burst


def load_jobs():
    with data_path("workload.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        Job(row["name"], int(row["arrival"]), int(row["burst"]), int(row["priority"]))
        for row in rows
    ]


jobs = load_jobs()
print("读入作业：", len(jobs), "个")
print("总运行时间：", sum(job.burst for job in jobs), "个时间单位")
for job in jobs:
    print(f"  {job.name}: 到达 {job.arrival}，运行 {job.burst}，优先级 {job.priority}")


class Scheduler:
    def __init__(self, quantum=2):
        self.quantum = quantum
        self.ready = queue.Queue()
        self.jobs = []
        self.pending = []
        self.index = 0
        self.time = 0
        self.timeline = []

    def load(self, jobs):
        self.jobs = list(jobs)
        self.pending = sorted(self.jobs, key=lambda job: (job.arrival, job.name))
        self.index = 0
        self.time = 0
        self.timeline = []
        self.ready = queue.Queue()

    def admit(self, now):
        while self.index < len(self.pending) and self.pending[self.index].arrival <= now:
            self.ready.put(self.pending[self.index])
            self.index += 1

    def run(self):
        self.admit(0)
        while self.index < len(self.pending) or not self.ready.empty():
            if self.ready.empty():
                self.time = self.pending[self.index].arrival
                self.admit(self.time)
                continue
            job = self.ready.get()
            if job.start < 0:
                job.start = self.time
            slice_time = min(self.quantum, job.remaining)
            start = self.time
            self.time += slice_time
            job.remaining -= slice_time
            self.timeline.append((job.name, start, self.time))
            self.admit(self.time)
            if job.remaining == 0:
                job.finish = self.time
            else:
                self.ready.put(job)
        return self.timeline

    def report(self):
        rows = []
        for job in self.jobs:
            waiting = job.finish - job.arrival - job.burst
            turnaround = job.finish - job.arrival
            rows.append({
                "name": job.name,
                "arrival": job.arrival,
                "burst": job.burst,
                "start": job.start,
                "finish": job.finish,
                "waiting": waiting,
                "turnaround": turnaround,
            })
        summary = {
            "average_waiting": sum(row["waiting"] for row in rows) / len(rows),
            "average_turnaround": sum(row["turnaround"] for row in rows) / len(rows),
        }
        return rows, summary


scheduler = Scheduler(quantum=2)
scheduler.load(jobs)


timeline = scheduler.run()
rows, summary = scheduler.report()

print("执行时间线：")
for name, start, end in timeline:
    print(f"  {start:>2}-{end:<2} {name}")

print("每个作业的指标：")
for row in rows:
    print(
        f"  {row['name']}: 开始 {row['start']:>2}，完成 {row['finish']:>2}，"
        f"等待 {row['waiting']:>2}，周转 {row['turnaround']:>2}"
    )

print(f"平均等待：{summary['average_waiting']:.2f}")
print(f"平均周转：{summary['average_turnaround']:.2f}")
print("所有作业都完成：", all(row["finish"] >= 0 for row in rows))


def run_with(quantum):
    sample = load_jobs()
    engine = Scheduler(quantum)
    engine.load(sample)
    timeline = engine.run()
    rows, summary = engine.report()
    return timeline, rows, summary


results = {}
for quantum in (1, 2, 4, 99):
    timeline, rows, summary = run_with(quantum)
    results[quantum] = (timeline, rows, summary)
    print(
        f"时间片 {quantum:>2}: 平均等待 {summary['average_waiting']:.2f}，"
        f"平均周转 {summary['average_turnaround']:.2f}"
    )


import matplotlib.pyplot as plt
from IPython.display import Image, display

job_names = [job.name for job in load_jobs()]
palette = ["#4C78A8", "#F2A65A", "#6BBF8A", "#B07AA1", "#D65A5A"]
colors = {name: palette[index % len(palette)] for index, name in enumerate(job_names)}

charts = [
    ("时间片 q=2", results[2][0]),
    ("时间片 q=99（等价于 FCFS）", results[99][0]),
]
max_time = max(end for _, timeline in charts for _, _, end in timeline)

fig, axes = plt.subplots(2, 1, figsize=(10, 4.8), sharex=True)
for ax, (label, timeline) in zip(axes, charts):
    for name, start, end in timeline:
        row = job_names.index(name)
        ax.barh(row, end - start, left=start, height=0.55,
                color=colors[name], edgecolor="white")
        if end - start >= 2:
            ax.text((start + end) / 2, row, name, ha="center", va="center",
                    color="white", fontsize=9)
    ax.set_yticks(range(len(job_names)))
    ax.set_yticklabels(job_names)
    ax.invert_yaxis()
    ax.set_title(label, loc="left", fontsize=11)
    ax.set_xlim(0, max_time + 1)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)

axes[-1].set_xlabel("时间")
fig.suptitle("迷你调度器的时间线对比")
fig.tight_layout()
figure_path = OUTPUT / "project-gantt.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
print("项目甘特图已保存：", figure_path.relative_to(Path.cwd()).as_posix())


rows = results[2][1]
report_path = OUTPUT / "scheduler-report.csv"
with report_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=["name", "arrival", "burst", "start", "finish", "waiting", "turnaround"],
    )
    writer.writeheader()
    writer.writerows(rows)


def no_overlap(timeline):
    ordered = sorted(timeline, key=lambda item: item[1])
    return all(
        ordered[index][2] <= ordered[index + 1][1]
        for index in range(len(ordered) - 1)
    )


longest = max(rows, key=lambda row: row["waiting"])
print("报表已写入：", report_path.relative_to(Path.cwd()).as_posix())
print("报表行数：", len(rows))
print(f"等待最久的作业：{longest['name']}，等待 {longest['waiting']} 个时间单位")
print("时间线无重叠：", no_overlap(results[2][0]))
print("所有作业都有完成时间：", all(row["finish"] >= 0 for row in rows))
print("验收通过：", no_overlap(results[2][0]) and all(row["finish"] >= 0 for row in rows))

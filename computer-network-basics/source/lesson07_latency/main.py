from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

output = Path("output")
output.mkdir(exist_ok=True)

components = [
    ("DNS 解析", 20, "#9DB4CE"),
    ("TCP 握手", 40, "#6C8EBF"),
    ("TLS 握手", 80, "#4C78A8"),
    ("等待首字节", 120, "#D6A354"),
    ("下载正文", 60, "#7FA37A"),
]
total = sum(item[1] for item in components)
print(f"一次请求的总耗时（示例，单位：毫秒）：{total}")
for name, cost, _ in components:
    print(f"{name:<10}{cost:>4} ms  占比 {cost / total:>6.1%}")

fig, ax = plt.subplots(figsize=(9, 2.8))
left = 0
for name, cost, color in components:
    ax.barh(["端到端"], [cost], left=left, color=color, height=0.5, label=f"{name} {cost} ms")
    ax.text(left + cost / 2, 0, str(cost), ha="center", va="center", fontsize=9, color="#222222")
    left += cost
ax.set_xlim(0, total * 1.02)
ax.set_xlabel("毫秒")
ax.set_title(f"一次请求的耗时构成：{total} ms")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=5, frameon=False, fontsize=8)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0)
fig.tight_layout()
figure_path = output / "latency-budget.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
print("耗时拆解图：", figure_path)


import socket
import statistics
import threading
import time

left, right = socket.socketpair()


def echo():
    while True:
        data = right.recv(64)
        if not data:
            break
        right.sendall(data)


thread = threading.Thread(target=echo, daemon=True)
thread.start()

samples = []
for _ in range(20):
    start = time.perf_counter()
    left.sendall(b"ping")
    left.recv(64)
    samples.append((time.perf_counter() - start) * 1_000_000)
left.close()
right.close()
thread.join(timeout=3)
print("往返次数：", len(samples))
print(f"平均 RTT：{statistics.mean(samples):.1f} 微秒")
print(f"最小 RTT：{min(samples):.1f} 微秒")
print(f"最大 RTT：{max(samples):.1f} 微秒")
print("回环没有真实链路，真实网络的 RTT 通常以毫秒计")


def seconds_for(size_mb, bandwidth_mbps, overhead=0.0):
    bits = size_mb * 8 * 1_000_000
    return bits / (bandwidth_mbps * 1_000_000) * (1 + overhead)


rows = [
    ("10 MB，100 Mbps，理想", seconds_for(10, 100)),
    ("10 MB，100 Mbps，15% 开销", seconds_for(10, 100, 0.15)),
    ("10 MB，20 Mbps，15% 开销", seconds_for(10, 20, 0.15)),
]
for label, seconds in rows:
    print(f"{label:<26}{seconds:>5.2f} 秒，吞吐约 {10 * 8 / seconds:.1f} Mbps")

rtt_ms = 100
bandwidth_mbps = 100
in_flight = bandwidth_mbps * 1_000_000 * (rtt_ms / 1000) / 8 / 1_000_000
print(f"100 Mbps、RTT {rtt_ms} ms，带宽延迟积约 {in_flight:.2f} MB")

latency = 0.2
for count in (1, 4):
    serial = latency * count
    concurrent = latency
    print(
        f"{count} 个请求，每个 {latency * 1000:.0f} ms："
        f"串行 {serial:.2f} 秒，并发 {concurrent:.2f} 秒"
    )
print("并发隐藏了等待，但没有突破带宽")

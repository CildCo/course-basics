from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

output = Path("output")
output.mkdir(exist_ok=True)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))

tcp = axes[0]
tcp.set_xlim(0, 10)
tcp.set_ylim(0, 10)
tcp.axis("off")
tcp.plot([2, 2], [1, 9], color="#4C78A8", linewidth=2)
tcp.plot([8, 8], [1, 9], color="#D64545", linewidth=2)
tcp.text(2, 9.35, "客户端", ha="center", fontsize=11)
tcp.text(8, 9.35, "服务端", ha="center", fontsize=11)
for y, label, start, end, color in [
    (7.6, "SYN", 2, 8, "#4C78A8"),
    (6.2, "SYN + ACK", 8, 2, "#D64545"),
    (4.8, "ACK", 2, 8, "#4C78A8"),
    (3.2, "数据", 2, 8, "#6B8E6B"),
]:
    tcp.annotate(
        "",
        xy=(end, y),
        xytext=(start, y),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.6),
    )
    tcp.text(5, y + 0.18, label, ha="center", fontsize=9, color=color)
tcp.set_title("TCP：先三次握手，再传数据")

udp = axes[1]
udp.set_xlim(0, 10)
udp.set_ylim(0, 10)
udp.axis("off")
udp.plot([2, 2], [1, 9], color="#4C78A8", linewidth=2)
udp.plot([8, 8], [1, 9], color="#D64545", linewidth=2)
udp.text(2, 9.35, "客户端", ha="center", fontsize=11)
udp.text(8, 9.35, "服务端", ha="center", fontsize=11)
for y, label, start, end, color in [
    (6.6, "数据报", 2, 8, "#4C78A8"),
    (5.0, "响应（可能没有）", 8, 2, "#D64545"),
]:
    udp.annotate(
        "",
        xy=(end, y),
        xytext=(start, y),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.6),
    )
    udp.text(5, y + 0.18, label, ha="center", fontsize=9, color=color)
udp.text(5, 2.4, "没有握手，没有重传，也不保证顺序", ha="center", fontsize=9)
udp.set_title("UDP：直接发，不握手")

fig.tight_layout()
figure_path = output / "tcp-udp.png"
fig.savefig(figure_path, dpi=120, bbox_inches="tight")
display(Image(filename=str(figure_path)))
plt.close(fig)
print("示意图已保存：", figure_path)


import socket
import threading

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
server.listen(1)
port = server.getsockname()[1]
received = []
accepted = []


def serve():
    conn, addr = server.accept()
    accepted.append(addr)
    with conn:
        for _ in range(3):
            data = conn.recv(1024)
            if not data:
                break
            received.append(data.decode("utf-8"))
            conn.sendall(b"ack:" + data)
    server.close()


thread = threading.Thread(target=serve, daemon=True)
thread.start()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(3)
client.connect(("127.0.0.1", port))
local_port = client.getsockname()[1]
peer = client.getpeername()
for text in ["first", "second", "third"]:
    client.sendall(text.encode("utf-8"))
    reply = client.recv(1024).decode("utf-8")
    print(f"发送 {text:<8}收到 {reply}")
client.close()
thread.join(timeout=3)
print("服务端接受连接：", accepted[0])
print("客户端本地端口：", local_port)
print("客户端连接的对端：", peer)
print("服务端按顺序收到：", received)


import socket
import threading

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(("127.0.0.1", 0))
udp_server.settimeout(3)
udp_port = udp_server.getsockname()[1]
records = []


def serve_udp():
    for _ in range(2):
        data, addr = udp_server.recvfrom(1024)
        records.append((data.decode("utf-8"), addr[1]))
        udp_server.sendto(b"pong:" + data, addr)
    udp_server.close()


thread = threading.Thread(target=serve_udp, daemon=True)
thread.start()

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(3)
for text in ["ping-1", "ping-2"]:
    client.sendto(text.encode("utf-8"), ("127.0.0.1", udp_port))
    data, addr = client.recvfrom(1024)
    print("客户端收到", data.decode("utf-8"), "来自", addr)
client.close()
thread.join(timeout=3)
print("服务端记录（内容，来源端口）：", records)
print("UDP 客户端全程没有 connect，也不需要知道对端是否在线")

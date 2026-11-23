import ipaddress

network = ipaddress.ip_network("192.168.1.0/24")
print("网段：", network)
print("地址总数：", network.num_addresses)
print("可用主机数：", network.num_addresses - 2)
print("前四个主机地址：", [str(ip) for ip in list(network.hosts())[:4]])
for text in ["192.168.1.10", "192.168.2.10", "10.0.0.5"]:
    ip = ipaddress.ip_address(text)
    print(f"{text:<16}是否在同一网段：{ip in network}")
print("IPv6 示例：", ipaddress.ip_network("2001:db8::/64"))


import socket

services = {80: "HTTP", 443: "HTTPS", 22: "SSH", 53: "DNS", 3306: "MySQL"}
for port, name in services.items():
    kind = "知名端口" if port < 1024 else "注册端口"
    print(f"{port:<6}{name:<8}{kind}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 0))
host, port = server.getsockname()
print("系统分配的本地地址：", (host, port))
server.close()
print("套接字已关闭，端口回到可用池")


import json
import socket
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


zone = json.loads(data_path("dns-zone.json").read_text(encoding="utf-8"))


def resolve(name):
    trail = []
    for _ in range(5):
        record = zone.get(name)
        if record is None:
            raise LookupError(f"没有记录：{name}")
        trail.append(f"{name} -> {record['type']} {record['value']}")
        if record["type"] == "A":
            return record["value"], trail
        name = record["value"]
    raise LookupError("CNAME 链过长")


address, trail = resolve("www.example.local")
print("模拟解析过程：")
for line in trail:
    print(" ", line)
print("最终地址：", address)
print("本机 hosts 解析 localhost：", socket.gethostbyname("localhost"))
print(
    "getaddrinfo 的 IPv4 结果：",
    socket.getaddrinfo(
        "localhost", 443, family=socket.AF_INET, type=socket.SOCK_STREAM
    )[0][4],
)

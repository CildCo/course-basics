from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import socket
import threading

stop = threading.Event()
udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(("127.0.0.1", 0))
udp_server.settimeout(0.2)


def serve():
    while not stop.is_set():
        try:
            data, address = udp_server.recvfrom(1024)
        except socket.timeout:
            continue
        text = data.decode("utf-8")
        print("服务端收到：", text, "来自", address[1])
        udp_server.sendto(("udp-echo: " + text).encode("utf-8"), address)


thread = threading.Thread(target=serve, daemon=True)
thread.start()
print("UDP 服务端端口：", udp_server.getsockname()[1])


client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(2)
try:
    for index in range(3):
        message = f"消息{index + 1}"
        client.sendto(message.encode("utf-8"), udp_server.getsockname())
        reply, address = client.recvfrom(1024)
        print("客户端发送：", message)
        print("客户端收到：", reply.decode("utf-8"))
finally:
    client.close()


stop.set()
thread.join(timeout=3)
udp_server.close()
print("UDP 服务端已关闭")

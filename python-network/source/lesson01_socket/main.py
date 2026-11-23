from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import socket

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("TCP 套接字：", tcp_socket.family.name, tcp_socket.type.name)
print("UDP 套接字：", udp_socket.family.name, udp_socket.type.name)
tcp_socket.close()
udp_socket.close()
print("两个套接字都已关闭")


probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
probe.bind(("127.0.0.1", 0))
address = probe.getsockname()
print("绑定到：", address)
print("端口由系统分配：", address[1] > 0)
probe.close()


print("本机回环地址：", socket.gethostbyname("localhost"))
print("HTTP 默认端口：", socket.getservbyname("http"))
print("HTTPS 默认端口：", socket.getservbyname("https"))

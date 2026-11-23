import socket
import threading

response_body = b'{"message": "hello from raw tcp"}'
response = (
    b"HTTP/1.0 200 OK\r\n"
    b"Content-Type: application/json; charset=utf-8\r\n"
    + f"Content-Length: {len(response_body)}\r\n".encode("utf-8")
    + b"Connection: close\r\n\r\n"
    + response_body
)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
server.listen(1)
port = server.getsockname()[1]
seen = []


def serve_once():
    conn, addr = server.accept()
    with conn:
        request = conn.recv(4096)
        seen.append(request.decode("utf-8", errors="replace"))
        conn.sendall(response)
    server.close()


thread = threading.Thread(target=serve_once, daemon=True)
thread.start()
print("服务端监听端口：", port)


import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(3)
chunks = []
try:
    client.connect(("127.0.0.1", port))
    request = (
        b"GET /hello HTTP/1.0\r\n"
        b"Host: localhost\r\n"
        b"Connection: close\r\n\r\n"
    )
    client.sendall(request)
    while True:
        chunk = client.recv(1024)
        if not chunk:
            break
        chunks.append(chunk)
finally:
    client.close()

thread.join(timeout=3)
raw = b"".join(chunks)
print("收到分片数：", len(chunks))
print("响应字节数：", len(raw))
print("服务端看到的第一行：", seen[0].splitlines()[0])
print("客户端拼出的响应：")
print(raw.decode("utf-8"))


import socket

probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
probe.settimeout(1)
try:
    probe.connect(("127.0.0.1", port))
    print("端口上还有服务在监听")
except ConnectionRefusedError:
    print("连接被拒绝：对方明确返回没有这个服务")
except TimeoutError:
    print("连接超时：1 秒内没有收到任何回应")
    print("本机防火墙可能直接丢包，不同系统的表现不一样")
finally:
    probe.close()
print("无论拒绝还是超时，结论一致：连接没有建立")

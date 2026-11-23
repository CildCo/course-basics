from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import socket
import socketserver
import threading


class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data = self.request.recv(1024)
            if not data:
                break
            text = data.decode("utf-8")
            print("服务端收到：", text)
            self.request.sendall(("echo: " + text).encode("utf-8"))


class EchoServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


server = EchoServer(("127.0.0.1", 0), EchoHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
print("服务端监听：", server.server_address)


def tcp_request(message):
    client = socket.create_connection(
        ("127.0.0.1", server.server_address[1]), timeout=3
    )
    try:
        client.sendall(message.encode("utf-8"))
        reply = client.recv(1024)
        print("客户端发送：", message)
        print("客户端收到：", reply.decode("utf-8"))
    finally:
        client.close()


tcp_request("你好，服务器")
tcp_request("第二条消息")


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("TCP 服务端已关闭")

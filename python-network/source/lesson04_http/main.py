from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            payload = {"status": "ok", "service": "local-demo"}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
            status = 200
        elif self.path == "/":
            body = "<h1>本地 HTTP 服务</h1><p>访问 /health 查看状态</p>".encode("utf-8")
            content_type = "text/html; charset=utf-8"
            status = 200
        else:
            body = json.dumps({"error": "not found"}, ensure_ascii=False).encode("utf-8")
            content_type = "application/json; charset=utf-8"
            status = 404
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
print("HTTP 服务地址：", f"http://127.0.0.1:{server.server_address[1]}")


import http.client

connection = http.client.HTTPConnection(
    "127.0.0.1", server.server_address[1], timeout=3
)
try:
    connection.request("GET", "/health")
    response = connection.getresponse()
    print("状态：", response.status, response.reason)
    print("Content-Type：", response.getheader("Content-Type"))
    print("Content-Length：", response.getheader("Content-Length"))
    print("正文：", response.read().decode("utf-8"))
finally:
    connection.close()


connection = http.client.HTTPConnection(
    "127.0.0.1", server.server_address[1], timeout=3
)
try:
    connection.request("GET", "/")
    response = connection.getresponse()
    body = response.read().decode("utf-8")
    print("状态：", response.status)
    print("正文长度：", len(body))
    print("正文前 30 个字符：", body[:30])
finally:
    connection.close()


connection = http.client.HTTPConnection(
    "127.0.0.1", server.server_address[1], timeout=3
)
try:
    connection.request("GET", "/missing")
    response = connection.getresponse()
    body = response.read().decode("utf-8")
    print("状态：", response.status)
    print("正文：", body)
finally:
    connection.close()


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地 HTTP 服务已关闭")

import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/hello":
            body = json.dumps({"message": "hello"}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
port = server.server_address[1]
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

print("服务监听在 127.0.0.1 的随机端口：", port > 0)


connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
connection.request("GET", "/hello", headers={"Accept": "application/json"})
response = connection.getresponse()
body = response.read().decode("utf-8")

print("请求行：GET /hello HTTP/1.1")
print("Host：127.0.0.1（随机端口）")
print("响应状态：", response.status, response.reason)
print("Content-Type：", response.getheader("Content-Type"))
print("Content-Length：", response.getheader("Content-Length"))
print("响应体：", body)
connection.close()


connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
connection.request("GET", "/missing")
response = connection.getresponse()
print("请求不存在的路径：", response.status, response.reason)
print("响应体是 HTML：", b"<html" in response.read().lower())
connection.close()


server.shutdown()
thread.join(timeout=5)
server.server_close()

print("服务已关闭：", not thread.is_alive())

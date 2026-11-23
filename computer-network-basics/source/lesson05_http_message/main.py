import json

body = json.dumps({"prompt": "hello"}, ensure_ascii=False).encode("utf-8")
request = (
    b"POST /api/chat HTTP/1.1\r\n"
    b"Host: localhost\r\n"
    b"Content-Type: application/json\r\n"
    + f"Content-Length: {len(body)}\r\n".encode("utf-8")
    + b"Connection: close\r\n\r\n"
    + body
)
print(request.decode("utf-8"))
print("空行位置：", request.index(b"\r\n\r\n"))
print("总字节数：", len(request))
print("其中正文：", len(body), "字节")


import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "LocalApi/1.0"
    sys_version = ""

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/hello":
            self._send_json(200, {"message": "hello", "method": "GET"})
        elif self.path == "/login":
            self.send_response(302)
            self.send_header("Location", "/hello")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._send_json(404, {"error": "not found", "path": self.path})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid json"})
            return
        self._send_json(200, {"echo": payload, "bytes": length})

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
print("本地接口：", f"http://127.0.0.1:{server.server_address[1]}")


import http.client
import json

port = server.server_address[1]


def call(method, path, payload=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        return resp.status, resp.reason, dict(resp.getheaders()), data
    finally:
        conn.close()


for method, path, payload in [
    ("GET", "/hello", None),
    ("POST", "/api/echo", {"word": "网络"}),
    ("GET", "/login", None),
    ("GET", "/missing", None),
]:
    status, reason, headers, data = call(method, path, payload)
    print(f"{method} {path} -> {status} {reason}")
    print("  Content-Type:", headers.get("Content-Type"))
    print("  Content-Length:", headers.get("Content-Length"))
    if headers.get("Location"):
        print("  Location:", headers.get("Location"))
    print("  正文:", data)


raw = (
    b"HTTP/1.1 302 Found\r\n"
    b"Location: /login\r\n"
    b"Content-Type: text/plain\r\n"
    b"Content-Length: 9\r\n"
    b"\r\n"
    b"redirect!"
)

head, _, body = raw.partition(b"\r\n\r\n")
lines = head.decode("utf-8").split("\r\n")
status_line = lines[0]
headers = dict(line.split(": ", 1) for line in lines[1:])
print("状态行：", status_line)
print("响应头：", headers)
print("正文：", body.decode("utf-8"))
print("正文长度与头部声明一致：", len(body) == int(headers["Content-Length"]))

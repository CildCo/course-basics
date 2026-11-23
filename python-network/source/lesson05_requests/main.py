from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

items = [
    {"id": 1, "name": "键盘"},
    {"id": 2, "name": "鼠标"},
]


class JsonHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/items":
            self.send_json(200, {"items": items})
        elif self.path == "/items/1":
            self.send_json(200, items[0])
        elif self.path == "/items/999":
            self.send_json(404, {"error": "没有这个商品"})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        created = {"id": 99, "name": payload.get("name", "未命名")}
        self.send_json(201, created)

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), JsonHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base_url = f"http://127.0.0.1:{server.server_address[1]}"
print("本地接口：", base_url)


import requests

response = requests.get(base_url + "/items", timeout=3)
print(f"GET 状态码：{response.status_code}")
print("商品数量：", len(response.json()["items"]))
print("第一条：", response.json()["items"][0])

created = requests.post(base_url + "/items", json={"name": "显示器"}, timeout=3)
print(f"POST 状态码：{created.status_code}")
print("返回内容：", created.json())


try:
    missing = requests.get(base_url + "/items/999", timeout=3)
    missing.raise_for_status()
except requests.HTTPError as error:
    print("捕获状态码错误：", error)

blackhole = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
blackhole.bind(("127.0.0.1", 0))
blackhole.listen(1)


def accept_and_wait():
    connection, _ = blackhole.accept()
    time.sleep(0.6)
    connection.close()


threading.Thread(target=accept_and_wait, daemon=True).start()
slow_url = f"http://127.0.0.1:{blackhole.getsockname()[1]}/"
try:
    requests.get(slow_url, timeout=0.2)
except requests.Timeout:
    print("捕获超时：0.2 秒内没有响应")
finally:
    blackhole.close()


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地接口已关闭")

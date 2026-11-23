import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

def serve(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread

def request(server, path, method="GET", data=None, headers=None):
    url = f"http://127.0.0.1:{server.server_address[1]}{path}"
    body = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.headers.get("Content-Type"), response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get("Content-Type"), error.read().decode("utf-8")

def stop(server):
    server.shutdown()
    server.server_close()


routes = [
    ("GET", "/todos", "列出待办"),
    ("POST", "/todos", "新增待办"),
    ("GET", "/todos/1", "查看一条"),
    ("PUT", "/todos/1", "更新一条"),
    ("DELETE", "/todos/1", "删除一条"),
]
for method, path, description in routes:
    print(f"{method:6s} {path:12s} {description}")


bad = ["/getTodos", "/addTodo", "/deleteTodo"]
good = ["GET /todos", "POST /todos", "DELETE /todos/1"]
print("不推荐：", bad)
print("推荐：", good)

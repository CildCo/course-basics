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


todos = [{"id": 1, "title": "学 HTTP", "done": False}]

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.send_json(200, {"ok": True, "data": todos})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        item = {"id": len(todos) + 1, "title": payload.get("title", ""), "done": False}
        todos.append(item)
        self.send_json(201, {"ok": True, "data": item})

    def log_message(self, *args):
        pass

server, thread = serve(Handler)
try:
    print("列表：", request(server, "/todos")[2])
    print("新增：", request(server, "/todos", method="POST", data={"title": "写练习"}, headers={"Content-Type": "application/json"})[2])
    print("列表：", request(server, "/todos")[2])
finally:
    stop(server)


print("下一步：把 todos 换成数据库，把 Handler 换成 FastAPI")

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


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        token = self.headers.get("Authorization", "")
        if token != "Bearer secret":
            self.send_json(401, {"ok": False, "error": "unauthorized"})
            return
        self.send_json(200, {"ok": True, "data": "只有登录用户能看到"})

    def log_message(self, *args):
        pass

server, thread = serve(Handler)
try:
    print("无 token：", request(server, "/private"))
    print("有 token：", request(server, "/private", headers={"Authorization": "Bearer secret"}))
finally:
    stop(server)


print("401 Unauthorized：没有登录或 token 无效")
print("403 Forbidden：已登录，但权限不够")

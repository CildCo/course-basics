import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LabHandler(BaseHTTPRequestHandler):
    server_version = "LocalLab/1.0"
    sys_version = ""

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "lab"})
        elif self.path == "/items":
            self._send_json(
                200,
                {"items": [{"id": 1, "name": "网线"}, {"id": 2, "name": "交换机"}]},
            )
        else:
            self._send_json(404, {"error": "not found", "path": self.path})

    def do_POST(self):
        if self.path != "/echo":
            self._send_json(404, {"error": "not found", "path": self.path})
            return
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


server = ThreadingHTTPServer(("127.0.0.1", 0), LabHandler)
port = server.server_address[1]
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
print(f"实验服务已启动：http://127.0.0.1:{port}")


import http.client
import json
import socket
import time


def check_address(host):
    try:
        return {"ok": True, "address": socket.gethostbyname(host)}
    except socket.gaierror as exc:
        return {"ok": False, "error": str(exc)}


def check_port(host, port, timeout=1.0):
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(timeout)
    start = time.perf_counter()
    try:
        code = probe.connect_ex((host, port))
    finally:
        probe.close()
    return {
        "ok": code == 0,
        "connect_ex": code,
        "ms": round((time.perf_counter() - start) * 1000, 2),
    }


def check_request(host, port, path, method="GET", payload=None):
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    conn = http.client.HTTPConnection(host, port, timeout=3)
    start = time.perf_counter()
    try:
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        parsed = None
        if (resp.getheader("Content-Type") or "").startswith("application/json"):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None
        return {
            "ok": 200 <= resp.status < 300,
            "status": resp.status,
            "content_type": resp.getheader("Content-Type"),
            "bytes": len(raw),
            "json": parsed,
            "ms": elapsed,
        }
    finally:
        conn.close()


checks = {
    "address": check_address("localhost"),
    "port": check_port("127.0.0.1", port),
    "health": check_request("127.0.0.1", port, "/health"),
    "items": check_request("127.0.0.1", port, "/items"),
    "echo": check_request("127.0.0.1", port, "/echo", "POST", {"from": "client"}),
    "missing": check_request("127.0.0.1", port, "/missing"),
}
for name, result in checks.items():
    print(f"{name:<8}ok={str(result['ok']):<6}{result}")


from pathlib import Path

health = checks["health"]
items = checks["items"]
echo = checks["echo"]
missing = checks["missing"]

verdict = {
    "地址可解析": checks["address"]["ok"],
    "端口可连接": checks["port"]["ok"],
    "健康检查返回 200": health["status"] == 200,
    "健康检查内容正确": bool(health["json"]) and health["json"].get("status") == "ok",
    "列表接口是 JSON": (items["content_type"] or "").startswith("application/json"),
    "列表接口有两条数据": bool(items["json"]) and len(items["json"].get("items", [])) == 2,
    "回显正文一致": bool(echo["json"]) and echo["json"].get("echo") == {"from": "client"},
    "未知路径返回 404": missing["status"] == 404,
}

report = {
    "target": {"host": "127.0.0.1", "port": port},
    "checks": checks,
    "verdict": verdict,
    "passed": all(verdict.values()),
}
output = Path("output")
output.mkdir(exist_ok=True)
report_path = output / "http-report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print("体检结论：", "全部通过" if report["passed"] else "存在异常")
for item, ok in verdict.items():
    print(f"  {'通过' if ok else '失败'}  {item}")
print("报告文件：", report_path)
print("报告大小：", report_path.stat().st_size, "字节")

server.shutdown()
thread.join(timeout=5)
server.server_close()
print("实验服务已关闭")

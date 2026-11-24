from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
print("环境就绪")

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


payload = ("网络小工具示例\n" * 40).encode("utf-8")


class FileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/file":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), FileHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
open_port = server.server_address[1]

probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
probe.bind(("127.0.0.1", 0))
closed_port = probe.getsockname()[1]
probe.close()

print(f"服务端口 {open_port} 状态：{'开放' if port_open(open_port) else '关闭'}")
print(f"空闲端口 {closed_port} 状态：{'开放' if port_open(closed_port) else '关闭'}")


base_url = f"http://127.0.0.1:{open_port}"
response = requests.get(base_url + "/file", timeout=3)
response.raise_for_status()
target = output / "download.txt"
target.write_bytes(response.content)
print("状态码：", response.status_code)
print("Content-Length：", response.headers.get("Content-Length"))
print("实际下载字节：", len(response.content))
print("内容校验一致：", target.read_bytes() == payload)


report_lines = [
    "网络小工具报告",
    f"服务端口 {open_port}：{'开放' if port_open(open_port) else '关闭'}",
    f"空闲端口 {closed_port}：{'开放' if port_open(closed_port) else '关闭'}",
    f"下载地址：{base_url}/file",
    f"下载字节：{len(response.content)}",
    f"保存文件：{target.name}",
]
report = "\n".join(report_lines)
report_path = output / "report.txt"
report_path.write_text(report + "\n", encoding="utf-8")
print(report)


server.shutdown()
thread.join(timeout=5)
server.server_close()
print("本地服务已关闭")

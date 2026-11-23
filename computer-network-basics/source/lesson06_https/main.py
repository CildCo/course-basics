import hashlib
import hmac

message = b"transfer=100&to=alice"
tampered = b"transfer=900&to=alice"
key = b"demo-shared-key"

print("原始消息的 SHA-256：", hashlib.sha256(message).hexdigest())
print("被篡改后的 SHA-256：", hashlib.sha256(tampered).hexdigest())
print("两者是否相同：", hashlib.sha256(message).digest() == hashlib.sha256(tampered).digest())
print("用共享密钥计算 HMAC：", hmac.new(key, message, hashlib.sha256).hexdigest()[:32], "...")
print("换一把密钥计算 HMAC：", hmac.new(b"wrong-key", message, hashlib.sha256).hexdigest()[:32], "...")
print("哈希能发现改动，HMAC 还能确认改动者没有密钥")


import socket
import ssl
import threading
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


cert_file = data_path("localhost-cert.pem")
key_file = data_path("localhost-key.pem")
server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_context.load_cert_chain(cert_file, key_file)


def start_tls_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    def serve():
        raw, _ = server.accept()
        try:
            with server_context.wrap_socket(raw, server_side=True) as conn:
                conn.sendall(b"secure:" + conn.recv(1024))
        except ssl.SSLError:
            # 客户端拒绝证书时会主动断开，这里不需要额外处理
            pass
        finally:
            server.close()

    threading.Thread(target=serve, daemon=True).start()
    return port


port = start_tls_server()
client_context = ssl.create_default_context(cafile=str(cert_file))
with socket.create_connection(("127.0.0.1", port)) as raw:
    with client_context.wrap_socket(raw, server_hostname="localhost") as tls:
        peer = tls.getpeercert()
        print("协议版本：", tls.version())
        print("加密套件：", tls.cipher()[0])
        print("证书主题：", dict(item[0] for item in peer["subject"]))
        print("颁发者：", dict(item[0] for item in peer["issuer"]))
        print("有效期至：", peer["notAfter"])
        print("备用名称：", peer["subjectAltName"])
        tls.sendall(b"hello over tls")
        print("服务端回复：", tls.recv(1024).decode("utf-8"))


import socket
import ssl

wrong_port = start_tls_server()
context = ssl.create_default_context(cafile=str(cert_file))
try:
    with socket.create_connection(("127.0.0.1", wrong_port)) as raw:
        with context.wrap_socket(raw, server_hostname="wrong.example") as tls:
            print("不该走到这里")
except ssl.SSLCertVerificationError as exc:
    print("证书校验失败：", exc.verify_message)
    print("原因：证书上的名字是 localhost，与访问的 wrong.example 不一致")

insecure_port = start_tls_server()
insecure = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
insecure.check_hostname = False
insecure.verify_mode = ssl.CERT_NONE
with socket.create_connection(("127.0.0.1", insecure_port)) as raw:
    with insecure.wrap_socket(raw, server_hostname="wrong.example") as tls:
        tls.sendall(b"hello")
        print("跳过校验后依然收到：", tls.recv(1024).decode("utf-8"))
        print("但无法确认对方身份，这正是中间人攻击的机会")

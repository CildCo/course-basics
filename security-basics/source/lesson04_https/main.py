import ssl

print("OpenSSL:", ssl.OPENSSL_VERSION)
print("支持 TLS 1.3:", ssl.HAS_TLSv1_3)

context = ssl.create_default_context()
print("默认最低版本:", context.minimum_version.name)
print("默认校验证书:", context.verify_mode == ssl.CERT_REQUIRED)
print("默认检查主机名:", context.check_hostname)


import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

cert_dir = Path.cwd() / "output" / "certs"
cert_dir.mkdir(parents=True, exist_ok=True)
cert_path = cert_dir / "cert.pem"
key_path = cert_dir / "key.pem"

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
now = datetime.now(timezone.utc)
certificate = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - timedelta(days=1))
    .not_valid_after(now + timedelta(days=30))
    .add_extension(
        x509.SubjectAlternativeName(
            [
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]
        ),
        critical=False,
    )
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(key, hashes.SHA256())
)

cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
key_path.write_bytes(
    key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
)
print("证书:", cert_path.name, "| 私钥:", key_path.name)
print("有效期至:", certificate.not_valid_after_utc.date())


import socket
import threading


def serve_once(context):
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    state = {"error": None}

    def worker():
        try:
            raw, _ = server.accept()
            with context.wrap_socket(raw, server_side=True) as tls:
                tls.sendall(b"hello from local tls server")
        except Exception as exc:
            state["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            server.close()

    thread = threading.Thread(target=worker)
    thread.start()
    return port, thread, state


server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
server_context.load_cert_chain(str(cert_path), str(key_path))

trusted_context = ssl.create_default_context(cafile=str(cert_path))
port, thread, state = serve_once(server_context)
with socket.create_connection(("127.0.0.1", port), timeout=5) as raw:
    with trusted_context.wrap_socket(raw, server_hostname="127.0.0.1") as tls:
        print("验证通过，协议:", tls.version())
        print("收到:", tls.recv(1024).decode())
thread.join(timeout=5)


default_context = ssl.create_default_context()
port, thread, state = serve_once(server_context)
try:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as raw:
        with default_context.wrap_socket(raw, server_hostname="127.0.0.1"):
            print("不应走到这里")
except ssl.SSLCertVerificationError as exc:
    print("验证失败:", type(exc).__name__)
    print("错误码包含 CERTIFICATE_VERIFY_FAILED:", "CERTIFICATE_VERIFY_FAILED" in str(exc))
thread.join(timeout=5)

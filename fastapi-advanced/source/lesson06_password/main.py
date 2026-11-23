from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir() and (
            (base / "collection.json").exists() or (base / "README.md").exists()
        ):
            return base
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        return here.parent


def data_path(name: str) -> Path:
    return course_root() / "assets" / name


def output_dir() -> Path:
    target = course_root() / "output"
    target.mkdir(parents=True, exist_ok=True)
    return target

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000


def hash_password(
    password: str,
    *,
    salt: bytes | None = None,
    iterations: int = ITERATIONS,
) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iteration_text, salt_hex, digest_hex = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        iterations = int(iteration_text)
    except (ValueError, TypeError):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(candidate, expected)


stored = hash_password("demo123")
parts = stored.split("$")
print("存储格式:", parts[0], "| 迭代次数:", parts[1])
print("盐长度:", len(parts[2]) // 2, "字节 | 摘要长度:", len(parts[3]) // 2, "字节")
print("正确密码:", verify_password("demo123", stored))
print("错误密码:", verify_password("demo124", stored))


first = hash_password("demo123")
second = hash_password("demo123")
print("两次哈希相同:", first == second)
print("各自都能验证:", verify_password("demo123", first), verify_password("demo123", second))
print("盐不同:", first.split("$")[2][:8], second.split("$")[2][:8])


def needs_rehash(stored: str, target: int = ITERATIONS) -> bool:
    try:
        algorithm, iteration_text, *_ = stored.split("$")
    except ValueError:
        return True
    return algorithm != ALGORITHM or int(iteration_text) < target


legacy = hash_password("demo123", iterations=60_000)
print("旧强度需要升级:", needs_rehash(legacy))
print("新强度需要升级:", needs_rehash(stored))

tampered = stored[:-1] + ("0" if stored[-1] != "0" else "1")
print("被篡改的哈希:", verify_password("demo123", tampered))
print("格式损坏:", verify_password("demo123", "not-a-hash"))


USERS = {"demo": hash_password("demo123")}
DUMMY_HASH = hash_password("dummy-password")


def register(username: str, password: str) -> bool:
    if username in USERS:
        return False
    USERS[username] = hash_password(password)
    return True


def login(username: str, password: str) -> bool:
    stored = USERS.get(username, DUMMY_HASH)
    matched = verify_password(password, stored)
    return username in USERS and matched


print("注册:", register("alice", "alice-pass-1"))
print("重复注册:", register("alice", "alice-pass-1"))
print("登录成功:", login("alice", "alice-pass-1"))
print("登录失败:", login("alice", "alice-pass-2"))
print("用户不存在:", login("bob", "whatever"))

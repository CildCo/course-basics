from pathlib import Path


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

import hashlib
import hmac
import secrets

ITERATIONS = 200_000


def make_salt():
    return secrets.token_bytes(16)


def hash_password(password, salt=None):
    if salt is None:
        salt = make_salt()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS
    )
    return {"salt": salt.hex(), "hash": digest.hex(), "iterations": ITERATIONS}


record = hash_password("Pa55word!")
print("盐:", record["salt"])
print("盐长度:", len(record["salt"]), "字符")
print("哈希长度:", len(record["hash"]), "字符")
print("迭代次数:", record["iterations"])


def verify_password(password, record):
    salt = bytes.fromhex(record["salt"])
    expected = bytes.fromhex(record["hash"])
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, record["iterations"]
    )
    return hmac.compare_digest(digest, expected)


print("正确密码:", verify_password("Pa55word!", record))
print("错误密码:", verify_password("pa55word!", record))


weak = hashlib.md5(b"123456").hexdigest()
print("123456 的 MD5:", weak)
print("两个用户同密码，MD5 完全相同:", hashlib.md5(b"123456").hexdigest() == weak)

first = hash_password("123456")
second = hash_password("123456")
print("同一密码，PBKDF2 前 24 位:")
print(" ", first["hash"][:24], "...")
print(" ", second["hash"][:24], "...")
print("两个哈希相同:", first["hash"] == second["hash"])

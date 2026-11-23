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

import datetime as dt

import jwt

SECRET_KEY = "dev-secret-at-least-32-bytes-long-please"
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 30


def create_access_token(
    user_id: int,
    role: str,
    *,
    minutes: int = ACCESS_TOKEN_MINUTES,
) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(minutes=minutes),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


token = create_access_token(1, "user")
claims = decode_access_token(token)
print("Token 段数:", token.count(".") + 1)
print("解析结果:", {key: claims[key] for key in ("sub", "role")})
print("过期时间存在:", "exp" in claims)


expired = create_access_token(1, "user", minutes=-5)
try:
    decode_access_token(expired)
except jwt.ExpiredSignatureError:
    print("过期 Token: 已拒绝")

wrong_key = "another-secret-at-least-32-bytes-long!"
try:
    jwt.decode(token, wrong_key, algorithms=[ALGORITHM])
except jwt.InvalidSignatureError:
    print("错误密钥: 签名校验失败")

try:
    jwt.decode(token, SECRET_KEY, algorithms=["HS512"])
except jwt.InvalidAlgorithmError:
    print("算法不匹配: 已拒绝")

try:
    decode_access_token("not.a.token")
except jwt.InvalidTokenError as exc:
    print("格式错误:", type(exc).__name__)


import hashlib
import hmac

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
from pydantic import BaseModel

PASSWORD_ITERATIONS = 120_000
DEMO_SALT = b"fixed-demo-salt"


def hash_password(password: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        DEMO_SALT,
        PASSWORD_ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, digest_hex: str) -> bool:
    return hmac.compare_digest(hash_password(password), digest_hex)


USERS = {
    1: {"username": "demo", "password": hash_password("demo123"), "role": "user"},
    2: {"username": "admin", "password": hash_password("admin123"), "role": "admin"},
}

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="缺少 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token 已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = USERS.get(int(claims["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return {"id": int(claims["sub"]), "username": user["username"], "role": claims["role"]}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


class LoginIn(BaseModel):
    username: str
    password: str


app = FastAPI()


@app.post("/auth/token")
def login(payload: LoginIn):
    user_id = next(
        (key for key, row in USERS.items() if row["username"] == payload.username),
        None,
    )
    if user_id is None or not verify_password(payload.password, USERS[user_id]["password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user = USERS[user_id]
    return {
        "access_token": create_access_token(user_id, user["role"]),
        "token_type": "bearer",
    }


@app.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.get("/admin/users")
def admin_users(user: dict = Depends(require_admin)):
    return {
        "operator": user["username"],
        "users": [row["username"] for row in USERS.values()],
    }


print("认证应用已就绪")


client = TestClient(app)
print("无 Token:", client.get("/me").status_code)

bad = client.post("/auth/token", json={"username": "demo", "password": "wrong"})
print("密码错误:", bad.status_code, bad.json())

login = client.post("/auth/token", json={"username": "demo", "password": "demo123"})
print("登录:", login.status_code, login.json()["token_type"])
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("当前用户:", client.get("/me", headers=headers).json())
print("普通用户访问管理接口:", client.get("/admin/users", headers=headers).status_code)

expired = create_access_token(1, "user", minutes=-1)
expired_response = client.get("/me", headers={"Authorization": f"Bearer {expired}"})
print("过期 Token:", expired_response.status_code, expired_response.json())

admin_login = client.post("/auth/token", json={"username": "admin", "password": "admin123"})
admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
print("管理员访问:", client.get("/admin/users", headers=admin_headers).json())

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
from pydantic import BaseModel

class Login(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    role: str


USERS = {
    "demo": {"password": "demo123", "role": "user"},
    "admin": {"password": "admin123", "role": "admin"},
}
TOKENS = {"token-demo": "demo", "token-admin": "admin"}

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization 头",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = TOKENS.get(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(username=username, role=USERS[username]["role"])


app = FastAPI()


@app.post("/auth/token")
def login(payload: Login):
    account = USERS.get(payload.username)
    if account is None or account["password"] != payload.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"access_token": f"token-{payload.username}", "token_type": "bearer"}


@app.get("/me", response_model=User)
def me(user: User = Depends(get_current_user)):
    return user


@app.get("/admin/users")
def admin_users(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return {"users": sorted(USERS)}


client = TestClient(app)
print("应用已就绪")


missing = client.get("/me")
print("不带 Token:", missing.status_code, missing.json())
print("WWW-Authenticate:", missing.headers.get("www-authenticate"))

bad = client.get("/me", headers={"Authorization": "Bearer wrong-token"})
print("错误 Token:", bad.status_code, bad.json())

bad_login = client.post("/auth/token", json={"username": "demo", "password": "wrong"})
print("密码错误:", bad_login.status_code, bad_login.json())


login = client.post("/auth/token", json={"username": "demo", "password": "demo123"})
print("登录成功:", login.status_code, login.json())

token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("当前用户:", client.get("/me", headers=headers).json())

admin_login = client.post("/auth/token", json={"username": "admin", "password": "admin123"})
admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
print("管理员访问用户列表:", client.get("/admin/users", headers=admin_headers).json())
print("普通用户访问管理接口:", client.get("/admin/users", headers=headers).status_code)

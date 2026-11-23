from fastapi import Depends, FastAPI, Header, Query, status
from fastapi.testclient import TestClient

app = FastAPI()


def pagination(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50)):
    return {"skip": skip, "limit": limit}


@app.get("/users")
def list_users(page: dict = Depends(pagination)):
    names = [f"用户{i}" for i in range(1, 26)]
    start = page["skip"]
    return {"page": page, "items": names[start:start + page["limit"]]}


class CurrentUser:
    def __init__(self, x_user: str = Header(default="guest")):
        self.name = x_user
        self.role = "admin" if x_user == "admin" else "reader"


@app.get("/profile")
def profile(user: CurrentUser = Depends(CurrentUser)):
    return {"name": user.name, "role": user.role}


def get_settings():
    print("加载配置")
    return {"app": "task-api", "version": "0.1.0"}


def version_info(settings: dict = Depends(get_settings)):
    return settings["version"]


@app.get("/about")
def about(settings: dict = Depends(get_settings), version: str = Depends(version_info)):
    return {"settings": settings, "version": version}


def db_session():
    print("打开数据库连接")
    try:
        yield {"connected": True}
    finally:
        print("关闭数据库连接")


@app.get("/db-check")
def db_check(db: dict = Depends(db_session)):
    return {"db": db}


client = TestClient(app)
print("应用已就绪")


print("分页:", client.get("/users?skip=5&limit=3").json())
print("默认分页:", client.get("/users").json()["page"])

print("默认用户:", client.get("/profile").json())
print("管理员:", client.get("/profile", headers={"X-User": "admin"}).json())

print("关于:", client.get("/about").json())
print("资源检查:", client.get("/db-check").json())

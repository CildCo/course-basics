import json
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select


class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool = False


class Todo(TodoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: str = Field(index=True)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    done: bool | None = None


class TodoPage(SQLModel):
    total: int
    skip: int
    limit: int
    items: list[Todo]


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


USERS = {
    "demo": {"password": "demo123", "role": "user"},
    "admin": {"password": "admin123", "role": "admin"},
}
TOKENS = {"token-demo": "demo", "token-admin": "admin"}

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credentials is None or credentials.credentials not in TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或缺失的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TOKENS[credentials.credentials]


app = FastAPI(title="待办 API", version="1.0.0")


@app.post("/auth/token", response_model=Token)
def login(payload: Login):
    account = USERS.get(payload.username)
    if account is None or account["password"] != payload.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return Token(access_token=f"token-{payload.username}", token_type="bearer")


@app.post("/todos", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(
    payload: TodoCreate,
    session: SessionDep,
    user: str = Depends(current_user),
):
    todo = Todo(**payload.model_dump(), owner=user)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.get("/todos", response_model=TodoPage)
def list_todos(
    session: SessionDep,
    user: str = Depends(current_user),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=20),
    done: bool | None = None,
    q: str | None = Query(default=None, max_length=20),
    sort: Literal["id", "id_desc", "title"] = "id",
):
    statement = select(Todo).where(Todo.owner == user)
    if done is not None:
        statement = statement.where(Todo.done == done)
    if q:
        statement = statement.where(Todo.title.contains(q))

    total = len(session.exec(statement).all())
    ordering = {
        "id": Todo.id,
        "id_desc": Todo.id.desc(),
        "title": Todo.title,
    }[sort]
    items = session.exec(statement.order_by(ordering).offset(skip).limit(limit)).all()
    return TodoPage(total=total, skip=skip, limit=limit, items=items)


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(
    todo_id: int,
    session: SessionDep,
    user: str = Depends(current_user),
):
    todo = session.get(Todo, todo_id)
    if todo is None or todo.owner != user:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    session: SessionDep,
    user: str = Depends(current_user),
):
    todo = session.get(Todo, todo_id)
    if todo is None or todo.owner != user:
        raise HTTPException(status_code=404, detail="待办不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    session: SessionDep,
    user: str = Depends(current_user),
):
    todo = session.get(Todo, todo_id)
    if todo is None or todo.owner != user:
        raise HTTPException(status_code=404, detail="待办不存在")
    session.delete(todo)
    session.commit()


client = TestClient(app)
print("待办 API 已就绪，路径:", list(client.get("/openapi.json").json()["paths"]))


login = client.post("/auth/token", json={"username": "demo", "password": "demo123"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("登录:", login.status_code, login.json())

unauthorized = client.post("/todos", json={"title": "未登录任务"})
print("未登录创建:", unauthorized.status_code, unauthorized.json())

for title in ["写周报", "整理需求", "修复登录问题"]:
    response = client.post("/todos", json={"title": title}, headers=headers)
    print("创建:", response.status_code, response.json())


first = client.get("/todos?limit=2", headers=headers)
print("第一页:", json.dumps(first.json(), ensure_ascii=False, indent=2))

second = client.get("/todos?skip=2&limit=2&sort=id_desc", headers=headers)
print("第二页:", [item["title"] for item in second.json()["items"]])
print("总数:", first.json()["total"])

completed = client.get("/todos?done=true", headers=headers)
print("已完成数量:", completed.json()["total"])

search = client.get("/todos?q=周报", headers=headers)
print("搜索“周报”:", [item["title"] for item in search.json()["items"]])


updated = client.patch("/todos/1", json={"done": True}, headers=headers)
print("完成第一条:", updated.status_code, updated.json())

renamed = client.patch("/todos/2", json={"title": "整理需求（周一前）"}, headers=headers)
print("重命名:", renamed.status_code, renamed.json()["title"])

admin_login = client.post("/auth/token", json={"username": "admin", "password": "admin123"})
admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
admin_create = client.post("/todos", json={"title": "管理员任务"}, headers=admin_headers)
print("管理员创建:", admin_create.status_code)

admin_list = client.get("/todos", headers=admin_headers).json()
print("管理员列表:", [item["title"] for item in admin_list["items"]])
print("管理员看 demo 的任务:", client.get("/todos/1", headers=admin_headers).status_code)

print("删除第三条:", client.delete("/todos/3", headers=headers).status_code)
print("删除后再查:", client.get("/todos/3", headers=headers).status_code)
print("剩余数量:", client.get("/todos", headers=headers).json()["total"])


summary = [
    ("POST /auth/token", login.status_code),
    ("POST /todos", 201),
    ("GET /todos", first.status_code),
    ("GET /todos/1", client.get("/todos/1", headers=headers).status_code),
    ("PATCH /todos/1", updated.status_code),
    ("DELETE /todos/3", 204),
]
for path, code_value in summary:
    print(f"{path:22s} {code_value}")

print("\n下一步可以扩展：")
print("- 用户注册与密码哈希")
print("- Token 过期与刷新")
print("- 按标签、截止日期筛选")
print("- 把 SQLite 换成 PostgreSQL，并加迁移脚本")

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

base = output_dir() / "todo_project"
(base / "routers").mkdir(parents=True, exist_ok=True)
(base / "tests").mkdir(parents=True, exist_ok=True)
(base / "__init__.py").write_text("", encoding="utf-8")
(base / "routers" / "__init__.py").write_text("", encoding="utf-8")

files = {}

files["database.py"] = """
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(url: str = "sqlite://"):
    options = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    if url in {"sqlite://", "sqlite:///:memory:"}:
        from sqlalchemy.pool import StaticPool

        options["poolclass"] = StaticPool
    return create_engine(url, **options)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
"""

files["models.py"] = """
import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime,
        default=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None),
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(60))
    done: Mapped[bool] = mapped_column(default=False)
"""

files["schemas.py"] = """
from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    done: bool | None = None


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
"""

files["security.py"] = """
import datetime as dt
import hashlib
import hmac
import os
import secrets

import jwt

ALGORITHM = "HS256"
SECRET_KEY = os.environ.get("APP_SECRET", "dev-secret-at-least-32-bytes-long-please")
ACCESS_TOKEN_MINUTES = 30
PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def create_access_token(user_id: int, username: str) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + dt.timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
"""

files["deps.py"] = """
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .models import User
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request):
    factory = request.app.state.session_factory
    with factory() as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
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
    user = db.get(User, int(claims["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
"""

files["routers/auth.py"] = """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing is not None:
        raise HTTPException(status_code=409, detail="用户名已存在")
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return TokenOut(access_token=create_access_token(user.id, user.username))
"""

files["routers/todos.py"] = """
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import Todo, User
from ..schemas import TodoIn, TodoOut, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


def owned_todo(db: Session, todo_id: int, user: User) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None or todo.owner_id != user.id:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@router.get("", response_model=list[TodoOut])
def list_todos(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Todo).where(Todo.owner_id == user.id).order_by(Todo.id)
    ).all()


@router.post("", response_model=TodoOut, status_code=201)
def create_todo(
    payload: TodoIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = Todo(owner_id=user.id, title=payload.title)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.get("/{todo_id}", response_model=TodoOut)
def get_todo(
    todo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return owned_todo(db, todo_id, user)


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = owned_todo(db, todo_id, user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    todo = owned_todo(db, todo_id, user)
    db.delete(todo)
    db.commit()
"""

files["main.py"] = """
from fastapi import FastAPI

from .database import Base, make_engine, make_session_factory
from .routers import auth, todos


def create_app(engine=None) -> FastAPI:
    engine = engine or make_engine()
    Base.metadata.create_all(engine)

    app = FastAPI(title="待办 API")
    app.state.session_factory = make_session_factory(engine)
    app.include_router(auth.router)
    app.include_router(todos.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
"""

files["tests/test_api.py"] = """
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from todo_project.main import create_app


@pytest.fixture()
def client(tmp_path):
    database = tmp_path / "app.db"
    engine = create_engine(
        f"sqlite:///{database.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    app = create_app(engine)
    with TestClient(app) as test_client:
        yield test_client


def register(client, username="demo", password="demo-pass-1"):
    response = client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def login(client, username="demo", password="demo-pass-1"):
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_register_and_duplicate(client):
    user = register(client)
    assert user == {"id": 1, "username": "demo"}
    again = client.post(
        "/auth/register",
        json={"username": "demo", "password": "another-pass"},
    )
    assert again.status_code == 409


def test_login_rejects_wrong_password(client):
    register(client)
    response = client.post(
        "/auth/login",
        json={"username": "demo", "password": "wrong-pass"},
    )
    assert response.status_code == 401


def test_todo_flow(client):
    register(client)
    headers = login(client)

    created = client.post("/todos", json={"title": "写接口文档"}, headers=headers)
    assert created.status_code == 201
    todo_id = created.json()["id"]

    listed = client.get("/todos", headers=headers).json()
    assert listed[0]["title"] == "写接口文档"

    updated = client.patch(f"/todos/{todo_id}", json={"done": True}, headers=headers)
    assert updated.json()["done"] is True

    deleted = client.delete(f"/todos/{todo_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/todos", headers=headers).json() == []


def test_requires_token(client):
    assert client.get("/todos").status_code == 401


def test_users_are_isolated(client):
    register(client, "alice", "alice-pass-1")
    register(client, "bob", "bob-pass-1")
    alice = login(client, "alice", "alice-pass-1")
    bob = login(client, "bob", "bob-pass-1")

    todo = client.post("/todos", json={"title": "alice 的待办"}, headers=alice).json()
    assert client.get(f"/todos/{todo['id']}", headers=bob).status_code == 404
    assert client.get("/todos", headers=bob).json() == []


def test_validation(client):
    register(client)
    headers = login(client)
    assert client.post("/todos", json={"title": ""}, headers=headers).status_code == 422
    bad_register = client.post(
        "/auth/register",
        json={"username": "x", "password": "short"},
    )
    assert bad_register.status_code == 422
"""

for name, content in files.items():
    target = base / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")

print("生成文件:", ", ".join(sorted(files)))


for path in sorted(base.rglob("*.py")):
    relative = path.relative_to(base).as_posix()
    print(relative, len(path.read_text(encoding="utf-8").splitlines()), "行")


import sys

root = str(output_dir())
if root not in sys.path:
    sys.path.insert(0, root)
for name in [key for key in sys.modules if key == "todo_project" or key.startswith("todo_project.")]:
    del sys.modules[name]

from fastapi.testclient import TestClient
from todo_project.main import create_app

client = TestClient(create_app())
print("健康检查:", client.get("/health").json())

registered = client.post(
    "/auth/register",
    json={"username": "demo", "password": "demo-pass-1"},
)
print("注册:", registered.status_code, registered.json())

login = client.post(
    "/auth/login",
    json={"username": "demo", "password": "demo-pass-1"},
)
print("登录:", login.status_code, login.json()["token_type"])

headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
created = client.post("/todos", json={"title": "完成项目验收"}, headers=headers)
print("创建待办:", created.status_code, created.json())
print("我的待办:", client.get("/todos", headers=headers).json())
print("未登录访问:", client.get("/todos").status_code)


import os
import subprocess
import sys

env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-q",
        "--color=no",
        "-p",
        "no:cacheprovider",
    ],
    cwd=base,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    env=env,
)
print("退出码:", result.returncode)
print(result.stdout.strip())
assert result.returncode == 0, result.stderr

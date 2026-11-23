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

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient
from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    role: Mapped[str] = mapped_column(String(20), default="user")


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(60))
    done: Mapped[bool] = mapped_column(default=False)


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

with Session(engine) as session:
    session.add_all(
        [
            User(id=1, username="demo", role="user"),
            User(id=2, username="admin", role="admin"),
            Todo(owner_id=1, title="整理接口文档"),
            Todo(owner_id=2, title="审查权限配置"),
        ]
    )
    session.commit()
print("种子数据已写入")


bearer = HTTPBearer(auto_error=False)
TOKENS = {"token-demo": 1, "token-admin": 2}


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.credentials not in TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或 Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, TOKENS[credentials.credentials])
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


print("依赖链: 路由 -> get_current_user -> get_db")
print("Token 映射:", TOKENS)


app = FastAPI()


@app.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}


@app.get("/todos")
def my_todos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Todo).where(Todo.owner_id == user.id)).all()
    return [{"id": row.id, "title": row.title, "done": row.done} for row in rows]


@app.get("/admin/stats")
def admin_stats(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    count = len(db.scalars(select(Todo)).all())
    return {"users": 2, "todos": count, "operator": user.username}


client = TestClient(app)
demo = {"Authorization": "Bearer token-demo"}
admin = {"Authorization": "Bearer token-admin"}

print("无 Token:", client.get("/me").status_code)
print("demo 当前用户:", client.get("/me", headers=demo).json())
print("demo 待办:", client.get("/todos", headers=demo).json())
print("demo 访问后台:", client.get("/admin/stats", headers=demo).status_code)
print("admin 访问后台:", client.get("/admin/stats", headers=admin).json())


def fake_admin() -> User:
    return User(id=99, username="测试管理员", role="admin")


app.dependency_overrides[get_current_user] = fake_admin
print("覆盖当前用户后:", client.get("/admin/stats", headers=demo).json())
app.dependency_overrides.clear()
print("清空覆盖后:", client.get("/admin/stats", headers=demo).status_code)

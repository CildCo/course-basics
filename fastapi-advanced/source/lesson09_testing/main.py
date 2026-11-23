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

base = output_dir() / "testing_demo"
(base / "tests").mkdir(parents=True, exist_ok=True)

app_source = """
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(60))
    done: Mapped[bool] = mapped_column(default=False)


class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as session:
        yield session


app = FastAPI()


@app.get("/todos", response_model=list[TodoOut])
def list_todos(db: Session = Depends(get_db)):
    return db.scalars(select(Todo).order_by(Todo.id)).all()


@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(payload: TodoIn, db: Session = Depends(get_db)):
    todo = Todo(title=payload.title)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="待办不存在")
    return todo


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {"total": db.scalar(select(func.count()).select_from(Todo))}
"""

test_source = """
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import Base, app, get_db


@pytest.fixture()
def client(tmp_path):
    database = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_and_read(client):
    created = client.post("/todos", json={"title": "写测试"})
    assert created.status_code == 201
    assert created.json()["id"] == 1

    fetched = client.get("/todos/1")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "写测试"


def test_list_order(client):
    client.post("/todos", json={"title": "第一条"})
    client.post("/todos", json={"title": "第二条"})
    titles = [row["title"] for row in client.get("/todos").json()]
    assert titles == ["第一条", "第二条"]


def test_validation_error(client):
    response = client.post("/todos", json={"title": ""})
    assert response.status_code == 422


def test_missing_todo(client):
    response = client.get("/todos/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "待办不存在"


def test_each_test_gets_empty_database(client):
    assert client.get("/stats").json() == {"total": 0}
"""

(base / "app.py").write_text(app_source.strip() + "\n", encoding="utf-8")
(base / "tests" / "test_api.py").write_text(test_source.strip() + "\n", encoding="utf-8")

print("应用文件:", (base / "app.py").relative_to(base))
print("测试文件:", (base / "tests" / "test_api.py").relative_to(base))


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
print("工作目录:", base.name)
print("退出码:", result.returncode)
print(result.stdout.strip())
assert result.returncode == 0, result.stderr

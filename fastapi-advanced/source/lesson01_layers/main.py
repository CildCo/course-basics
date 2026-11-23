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

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field


class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)


flat = FastAPI()
ROWS = {}
NEXT_ID = {"value": 1}


@flat.post("/todos", status_code=201)
def create_todo(payload: TodoIn):
    row = {"id": NEXT_ID["value"], "title": payload.title, "done": False}
    ROWS[row["id"]] = row
    NEXT_ID["value"] += 1
    return row


@flat.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    row = ROWS.get(todo_id)
    if row is None:
        raise HTTPException(status_code=404, detail="待办不存在")
    return row


client = TestClient(flat)
created = client.post("/todos", json={"title": "整理接口文档"})
print("创建:", created.status_code, created.json())
print("读取:", client.get("/todos/1").json())
print("不存在:", client.get("/todos/99").status_code)


package = output_dir() / "layered_app"
package.mkdir(parents=True, exist_ok=True)
(package / "__init__.py").write_text("", encoding="utf-8")

files = {}

files["db.py"] = """
class TodoStore:
    def __init__(self):
        self._rows = {}
        self._next_id = 1

    def list(self):
        return [dict(row) for row in self._rows.values()]

    def get(self, todo_id):
        row = self._rows.get(todo_id)
        return dict(row) if row else None

    def add(self, title):
        row = {"id": self._next_id, "title": title, "done": False}
        self._rows[row["id"]] = row
        self._next_id += 1
        return dict(row)

    def update(self, todo_id, changes):
        row = self._rows.get(todo_id)
        if row is None:
            return None
        row.update(changes)
        return dict(row)

    def delete(self, todo_id):
        return self._rows.pop(todo_id, None) is not None
"""

files["schemas.py"] = """
from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=60)


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    done: bool | None = None


class TodoRead(BaseModel):
    id: int
    title: str
    done: bool
"""

files["services.py"] = """
from . import db, schemas


class TodoService:
    def __init__(self, store: db.TodoStore):
        self.store = store

    def list_todos(self):
        return self.store.list()

    def get(self, todo_id):
        return self.store.get(todo_id)

    def create(self, payload: schemas.TodoCreate):
        return self.store.add(payload.title)

    def update(self, todo_id, payload: schemas.TodoUpdate):
        return self.store.update(todo_id, payload.model_dump(exclude_unset=True))

    def delete(self, todo_id):
        return self.store.delete(todo_id)
"""

files["routers.py"] = """
from fastapi import APIRouter, HTTPException, status

from . import schemas, services


def build_router(service: services.TodoService) -> APIRouter:
    router = APIRouter(prefix="/todos", tags=["todos"])

    @router.get("", response_model=list[schemas.TodoRead])
    def list_todos():
        return service.list_todos()

    @router.post("", response_model=schemas.TodoRead, status_code=status.HTTP_201_CREATED)
    def create_todo(payload: schemas.TodoCreate):
        return service.create(payload)

    @router.get("/{todo_id}", response_model=schemas.TodoRead)
    def get_todo(todo_id: int):
        row = service.get(todo_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="待办不存在")
        return row

    @router.patch("/{todo_id}", response_model=schemas.TodoRead)
    def update_todo(todo_id: int, payload: schemas.TodoUpdate):
        row = service.update(todo_id, payload)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="待办不存在")
        return row

    @router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_todo(todo_id: int):
        if not service.delete(todo_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="待办不存在")

    return router
"""

files["main.py"] = """
from fastapi import FastAPI

from . import db, routers, services


def create_app() -> FastAPI:
    service = services.TodoService(db.TodoStore())
    app = FastAPI(title="分层待办")
    app.include_router(routers.build_router(service))
    return app
"""

for name, content in files.items():
    (package / name).write_text(content.strip() + "\n", encoding="utf-8")

print("生成文件:", ", ".join(sorted(files)))


import sys

root = str(output_dir())
if root not in sys.path:
    sys.path.insert(0, root)
for name in [key for key in sys.modules if key == "layered_app" or key.startswith("layered_app.")]:
    del sys.modules[name]

from layered_app.main import create_app

client = TestClient(create_app())
created = client.post("/todos", json={"title": "整理接口文档"})
print("创建:", created.status_code, created.json())
print("读取:", client.get("/todos/1").json())
print("更新:", client.patch("/todos/1", json={"done": True}).json())
print("删除:", client.delete("/todos/1").status_code)
print("删除后:", client.get("/todos/1").status_code)


for name in ("main.py", "routers.py", "services.py", "db.py"):
    path = package / name
    print(f"{name}: {len(path.read_text(encoding='utf-8').splitlines())} 行")

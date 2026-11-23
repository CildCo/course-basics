from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    done: bool = False


class TaskCreate(SQLModel):
    title: str = Field(min_length=1, max_length=50)
    done: bool = False


class TaskUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    done: bool | None = None


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

app = FastAPI()


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: SessionDep):
    task = Task(**payload.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.get("/tasks", response_model=list[Task])
def list_tasks(session: SessionDep):
    return session.exec(select(Task)).all()


@app.patch("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate, session: SessionDep):
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    session.delete(task)
    session.commit()


with Session(engine) as session:
    session.add_all([Task(title="写周报"), Task(title="修 bug", done=True)])
    session.commit()

client = TestClient(app)
print("应用已就绪")


print("初始列表:", client.get("/tasks").json())

created = client.post("/tasks", json={"title": "整理需求"})
print("创建:", created.status_code, created.json())

all_tasks = client.get("/tasks").json()
print("当前数量:", len(all_tasks))


updated = client.patch("/tasks/3", json={"done": True})
print("更新:", updated.status_code, updated.json())

partial = client.patch("/tasks/3", json={"title": "整理需求（已完成）"})
print("只改标题:", partial.json())

missing = client.patch("/tasks/99", json={"done": True})
print("更新不存在:", missing.status_code, missing.json())

deleted = client.delete("/tasks/2")
print("删除:", deleted.status_code)
print("删除后再更新:", client.patch("/tasks/2", json={"done": True}).status_code)
print("剩余:", client.get("/tasks").json())

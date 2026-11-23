from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Query
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    done: bool = False
    priority: int = 3


class TaskPage(SQLModel):
    total: int
    skip: int
    limit: int
    items: list[Task]


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


@app.get("/tasks", response_model=TaskPage)
def list_tasks(
    session: SessionDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=20),
    done: bool | None = None,
    q: str | None = Query(default=None, max_length=20),
    sort: Literal["id", "title", "priority"] = "id",
):
    statement = select(Task)
    if done is not None:
        statement = statement.where(Task.done == done)
    if q:
        statement = statement.where(Task.title.contains(q))

    total = len(session.exec(statement).all())
    ordering = {
        "id": Task.id,
        "title": Task.title,
        "priority": Task.priority.desc(),
    }[sort]
    items = session.exec(statement.order_by(ordering).offset(skip).limit(limit)).all()
    return TaskPage(total=total, skip=skip, limit=limit, items=items)


with Session(engine) as session:
    session.add_all([
        Task(title=f"任务 {index:02d}", done=index % 3 == 0, priority=index % 5 + 1)
        for index in range(1, 26)
    ])
    session.commit()

client = TestClient(app)
print("已写入 25 条任务")


page1 = client.get("/tasks?limit=5").json()
print("总数:", page1["total"], "本页:", len(page1["items"]))
print([item["title"] for item in page1["items"]])

page5 = client.get("/tasks?skip=20&limit=5").json()
print("第 5 页:", [item["title"] for item in page5["items"]])

beyond = client.get("/tasks?skip=100").json()
print("超出范围:", beyond["items"])


done_page = client.get("/tasks?done=true&limit=3").json()
print("已完成:", done_page["total"], [item["title"] for item in done_page["items"]])

search = client.get("/tasks?q=任务 1").json()
print("包含“任务 1”:", search["total"])

by_priority = client.get("/tasks?sort=priority&limit=5").json()
print("优先级排序:", [(item["title"], item["priority"]) for item in by_priority["items"]])

invalid = client.get("/tasks?sort=price")
print("非法排序:", invalid.status_code)

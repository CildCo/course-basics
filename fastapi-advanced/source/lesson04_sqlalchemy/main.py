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

import json

from sqlalchemy import String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    priority: Mapped[int] = mapped_column(default=2)
    done: Mapped[bool] = mapped_column(default=False)

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "done": self.done,
        }


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)

seed = json.loads(data_path("seed_todos.json").read_text(encoding="utf-8"))
with Session(engine) as session:
    session.add_all([Todo(**row) for row in seed])
    session.commit()

with Session(engine) as session:
    rows = session.scalars(select(Todo).order_by(Todo.id)).all()
    print("种子数据:", len(rows), "条")
    for row in rows:
        print(row.as_dict())


with Session(engine) as session:
    todo = Todo(title="给列表接口加缓存", priority=5)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    print("新增:", todo.as_dict())

with Session(engine) as session:
    todo = session.get(Todo, 1)
    todo.done = True
    todo.priority = 3
    session.commit()
    print("更新:", todo.as_dict())

with Session(engine) as session:
    todo = session.get(Todo, 2)
    todo.title = "临时修改"
    session.flush()
    print("flush 后同会话可见:", session.get(Todo, 2).title)
    session.rollback()

with Session(engine) as session:
    print("rollback 后:", session.get(Todo, 2).title)

with Session(engine) as session:
    todo = session.get(Todo, 3)
    session.delete(todo)
    session.commit()

with Session(engine) as session:
    print("删除后剩余:", [row.id for row in session.scalars(select(Todo).order_by(Todo.id))])


with Session(engine) as session:
    pending = session.scalars(
        select(Todo)
        .where(Todo.done.is_(False))
        .order_by(Todo.priority.desc(), Todo.id)
    ).all()
    print("未完成:", [(row.title, row.priority) for row in pending])
    total = session.scalar(select(func.count()).select_from(Todo))
    print("总数:", total)

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text, default="")
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Note {self.id} {self.title!r} done={self.done}>"


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
print("已建表:", list(Base.metadata.tables))


from sqlalchemy import func

with Session(engine) as session:
    note = Note(title="整理需求", body="把零散想法写成条目")
    print("add 之前 id:", note.id)
    session.add(note)
    print("add 之后 id:", note.id)
    session.flush()
    print("flush 之后 id:", note.id)
    session.commit()
    print("commit 之后 id:", note.id)
    session.refresh(note)
    print("refresh 之后:", note)

with Session(engine) as session:
    session.add_all([Note(title="写测试", done=True), Note(title="发布")])
    session.commit()
    total = session.scalar(select(func.count()).select_from(Note))
    print("当前总数:", total)


with Session(engine) as session:
    note = session.get(Note, 1)
    print("读取:", note)
    note.done = True
    note.title = "整理需求（已完成）"
    session.commit()
    session.refresh(note)
    print("更新:", note)

with Session(engine) as session:
    note = session.get(Note, 2)
    session.delete(note)
    session.commit()
    remaining = session.scalars(select(Note).order_by(Note.id)).all()
    print("删除后:", remaining)


with Session(engine) as session:
    note = session.get(Note, 1)
    note.title = "只改内存"
    same_session = session.scalar(select(Note).where(Note.id == 1))
    print("同一会话:", same_session.title)

with Session(engine) as session:
    other_session = session.get(Note, 1)
    print("新会话:", other_session.title)

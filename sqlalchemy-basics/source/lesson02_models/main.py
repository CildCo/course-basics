from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    price: Mapped[float] = mapped_column(Float)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    summary: Mapped[str | None] = mapped_column(String(300), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r} price={self.price}>"


for column in Book.__table__.columns:
    print(f"{column.name:<12}{str(column.type):<14}主键={column.primary_key}")


from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import CreateTable

engine = create_engine("sqlite://")
print(CreateTable(Book.__table__).compile(engine))
Base.metadata.create_all(engine)

for column in inspect(engine).get_columns("books"):
    nullable = "NULL" if column["nullable"] else "NOT NULL"
    key = " PK" if column["primary_key"] else ""
    print(f"{column['name']:<12}{str(column['type']):<14}{nullable}{key}")


from sqlalchemy import select
from sqlalchemy.orm import Session

with Session(engine) as session:
    book = Book(title="数据库系统概念", price=128.0, summary=None)
    session.add(book)
    session.commit()
    session.refresh(book)

    print(book)
    print("入库时间:", book.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    print("summary:", book.summary)

with Session(engine) as session:
    found = session.scalar(select(Book).where(Book.title == "数据库系统概念"))
    print("查询结果:", repr(found))

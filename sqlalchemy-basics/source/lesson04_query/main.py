from datetime import date

from sqlalchemy import Date, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(30), index=True)
    views: Mapped[int] = mapped_column(default=0)
    published_on: Mapped[date] = mapped_column(Date)


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)

rows = [
    ("SQLAlchemy 2.x 入门", "后端", 320, date(2026, 9, 1)),
    ("分页查询的边界", "后端", 180, date(2026, 9, 3)),
    ("SQLite 索引实战", "数据库", 260, date(2026, 9, 5)),
    ("事务隔离级别", "数据库", 90, date(2026, 9, 8)),
    ("FastAPI 依赖注入", "后端", 410, date(2026, 9, 10)),
    ("用 pandas 清洗日志", "数据", 150, date(2026, 9, 12)),
    ("从 CSV 到数据库", "数据", 75, date(2026, 9, 15)),
    ("缓存与一致性", "后端", 230, date(2026, 9, 18)),
    ("查询计划怎么看", "数据库", 120, date(2026, 9, 20)),
    ("数据建模的三个误区", "数据", 60, date(2026, 9, 22)),
    ("连接池参数怎么配", "后端", 300, date(2026, 9, 25)),
    ("SQL 窗口函数", "数据库", 350, date(2026, 9, 28)),
]

with Session(engine) as session:
    session.add_all(
        [Article(title=t, category=c, views=v, published_on=d) for t, c, v, d in rows]
    )
    session.commit()

print("已写入文章:", len(rows))


stmt = (
    select(Article)
    .where(Article.views >= 200)
    .order_by(Article.views.desc(), Article.id)
    .limit(4)
)
print(stmt)
print()

with Session(engine) as session:
    for article in session.scalars(stmt):
        print(f"{article.id:>2}  {article.title}  ({article.category}, {article.views})")


from sqlalchemy import func, or_

with Session(engine) as session:
    stmt = (
        select(Article)
        .where(
            or_(Article.category == "数据", Article.title.like("%SQL%")),
            Article.views >= 100,
        )
        .order_by(Article.published_on.desc())
    )
    for article in session.scalars(stmt):
        print(article.published_on, article.title, article.category)

    backend_count = session.scalar(
        select(func.count())
        .select_from(Article)
        .where(Article.category.in_(["后端", "数据库"]))
    )
    print("后端与数据库文章合计:", backend_count)


def page(number, size=5):
    with Session(engine) as session:
        total = session.scalar(select(func.count()).select_from(Article))
        items = session.scalars(
            select(Article)
            .order_by(Article.published_on.desc(), Article.id.desc())
            .offset((number - 1) * size)
            .limit(size)
        ).all()
    return total, items


for page_no in (1, 2, 3):
    total, items = page(page_no)
    print(f"第 {page_no} 页，共 {total} 条")
    for article in items:
        print("  ", article.published_on, article.title)

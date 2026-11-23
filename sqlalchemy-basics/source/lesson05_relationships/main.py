from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    Table,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    body: Mapped[str] = mapped_column(Text, default="")
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped[Author] = relationship(back_populates="posts")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=post_tags, back_populates="posts"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    posts: Mapped[list[Post]] = relationship(
        secondary=post_tags, back_populates="tags"
    )


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)
print("表:", sorted(Base.metadata.tables))


with Session(engine) as session:
    lin = Author(name="林一")
    chen = Author(name="陈默")
    sql = Tag(name="SQL")
    backend = Tag(name="后端")

    session.add_all(
        [
            lin,
            chen,
            sql,
            backend,
            Post(title="SQLAlchemy 2.x 入门", author=lin, tags=[sql, backend]),
            Post(title="分页查询的边界", author=lin, tags=[backend]),
            Post(title="查询计划怎么看", author=chen, tags=[sql]),
        ]
    )
    session.commit()

    print("作者:", session.scalar(select(func.count()).select_from(Author)))
    print("文章:", session.scalar(select(func.count()).select_from(Post)))
    print("标签:", session.scalar(select(func.count()).select_from(Tag)))


from sqlalchemy.orm import selectinload

with Session(engine) as session:
    author = session.scalar(
        select(Author)
        .where(Author.name == "林一")
        .options(selectinload(Author.posts).selectinload(Post.tags))
    )
    print(author.name, "的文章:")
    for post in author.posts:
        print("  ", post.title, "->", [tag.name for tag in post.tags])

    tag = session.scalar(
        select(Tag).where(Tag.name == "SQL").options(selectinload(Tag.posts))
    )
    print("标签 SQL 下的文章:", [post.title for post in tag.posts])


stmt = (
    select(Tag.name, func.count(post_tags.c.post_id).label("post_count"))
    .join(post_tags, Tag.id == post_tags.c.tag_id)
    .group_by(Tag.name)
    .order_by(func.count(post_tags.c.post_id).desc(), Tag.name)
)

with Session(engine) as session:
    for name, count in session.execute(stmt):
        print(f"{name:<6}{count} 篇")

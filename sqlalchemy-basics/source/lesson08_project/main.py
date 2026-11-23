from pathlib import Path
import csv
import json
import tempfile
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)


class Base(DeclarativeBase):
    pass


post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    posts: Mapped[list["Post"]] = relationship(
        secondary=post_tags, back_populates="tags"
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text, default="")
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped[User] = relationship(back_populates="posts")
    tags: Mapped[list[Tag]] = relationship(
        secondary=post_tags, back_populates="posts"
    )


DB_DIR = Path(tempfile.mkdtemp(prefix="blog-layer-"))
engine = create_engine(f"sqlite:///{(DB_DIR / 'blog.db').as_posix()}")
Base.metadata.create_all(engine)
print("数据表:", sorted(Base.metadata.tables))
print("示例数据:", data_path("sample_posts.csv").name)


class BlogRepository:
    def __init__(self, engine):
        self.engine = engine

    def create_user(self, name, email):
        with Session(self.engine) as session:
            user = User(name=name, email=email)
            session.add(user)
            session.commit()
            return user.id

    def create_post(self, title, summary, author_name, tag_names, published=True):
        with Session(self.engine) as session:
            author = session.scalar(select(User).where(User.name == author_name))
            if author is None:
                raise ValueError(f"未知作者：{author_name}")

            tags = []
            for name in tag_names:
                tag = session.scalar(select(Tag).where(Tag.name == name))
                if tag is None:
                    tag = Tag(name=name)
                    session.add(tag)
                tags.append(tag)

            post = Post(
                title=title,
                summary=summary,
                published=published,
                author=author,
                tags=tags,
            )
            session.add(post)
            session.commit()
            return post.id

    def list_posts(self, page=1, page_size=3, tag=None):
        with Session(self.engine) as session:
            stmt = select(Post).where(Post.published.is_(True))
            count_stmt = select(func.count()).select_from(Post).where(
                Post.published.is_(True)
            )
            if tag:
                stmt = stmt.join(Post.tags).where(Tag.name == tag)
                count_stmt = (
                    count_stmt.join(Post.tags).where(Tag.name == tag)
                )
            total = session.scalar(count_stmt)
            items = session.scalars(
                stmt.options(selectinload(Post.author), selectinload(Post.tags))
                .order_by(Post.created_at.desc(), Post.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
            return total, items


repo = BlogRepository(engine)
print("仓储就绪:", type(repo).__name__)


def load_rows():
    path = data_path("sample_posts.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


rows = load_rows()
users = {}
for row in rows:
    users.setdefault(
        row["author"],
        row["author"].lower().replace(" ", ".") + "@example.com",
    )

for name, email in users.items():
    repo.create_user(name, email)

for row in rows:
    tags = [item.strip() for item in row["tags"].split("|") if item.strip()]
    repo.create_post(
        title=row["title"],
        summary=row["summary"],
        author_name=row["author"],
        tag_names=tags,
        published=row["published"] == "1",
    )

total, items = repo.list_posts(page=1, page_size=3)
print("导入文章:", len(rows))
print("已发布:", total)
for post in items:
    print(f"- {post.title} / {post.author.name} / {[tag.name for tag in post.tags]}")


for tag in ["数据库", "后端"]:
    total, items = repo.list_posts(page=1, page_size=5, tag=tag)
    print(f"标签 {tag}: {total} 篇")
    for post in items:
        print("  ", post.title)

with Session(engine) as session:
    author_rows = session.execute(
        select(User.name, func.count(Post.id))
        .join(Post, Post.author_id == User.id)
        .group_by(User.name)
        .order_by(func.count(Post.id).desc(), User.name)
    ).all()

report = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_posts": len(rows),
    "authors": [{"name": name, "posts": count} for name, count in author_rows],
}
report_path = OUTPUT / "blog_report.json"
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(report_path.read_text(encoding="utf-8"))

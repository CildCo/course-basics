import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import sys
from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir() and (base / "collection.json").exists():
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


print("课程目录:", course_root().name)

import json

spec = json.loads(data_path("sample_urls.json").read_text(encoding="utf-8"))
print("默认有效期:", spec["default_ttl_seconds"] // 86400, "天")
print("最大缓存时间:", spec["cache_max_age_seconds"], "秒")
print("保留别名:", ", ".join(spec["reserved_aliases"]))
for index, url in enumerate(spec["sample_urls"], 1):
    print(f"样例 {index}: {url}")


from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    target_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    visits: Mapped[int] = mapped_column(Integer, default=0)


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)

with Session(engine) as session:
    session.add(Link(code="abc123", target_url=spec["sample_urls"][0]))
    session.commit()
    row = session.scalar(select(Link).where(Link.code == "abc123"))
    print("字段:", [column.name for column in Link.__table__.columns])
    print("写入:", row.code, "->", row.target_url)
    print("初始访问数:", row.visits, "创建时间:", row.created_at.strftime("%Y-%m-%d %H:%M:%S"))

try:
    with Session(engine) as session:
        session.add(Link(code="abc123", target_url="https://example.com/other"))
        session.commit()
except IntegrityError:
    print("重复 code 被唯一约束拒绝")


from pydantic import BaseModel, Field, HttpUrl, ValidationError


class LinkCreate(BaseModel):
    target_url: HttpUrl
    custom_alias: str | None = Field(default=None, min_length=1, max_length=32)
    ttl_seconds: int | None = Field(default=None, ge=60, le=31_536_000)


valid = LinkCreate(target_url=spec["sample_urls"][1], ttl_seconds=3600)
print("通过:", valid.model_dump(mode="json"))

for payload in (
    {"target_url": "ftp://example.com/file"},
    {"target_url": spec["sample_urls"][0], "ttl_seconds": 5},
    {"target_url": spec["sample_urls"][0], "custom_alias": "x" * 40},
):
    try:
        LinkCreate(**payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        print("拒绝:", first["loc"], "-", first["msg"])

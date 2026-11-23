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

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base62(number: int) -> str:
    if number <= 0:
        raise ValueError("编号必须为正整数")
    digits = []
    while number:
        number, remainder = divmod(number, 62)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


for value in (1, 10, 11, 61, 62, 63, 1000):
    print(f"{value:>4} -> {encode_base62(value)}")


import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

spec = json.loads(data_path("sample_urls.json").read_text(encoding="utf-8"))


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


class LinkCreate(BaseModel):
    target_url: HttpUrl
    ttl_seconds: int | None = Field(default=None, ge=60, le=31_536_000)


class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str
    expires_at: datetime | None


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
BASE_URL = "http://127.0.0.1:8010"


def get_db():
    with SessionLocal() as session:
        yield session


app = FastAPI(title="短链接服务")


@app.post("/links", status_code=201, response_model=LinkOut)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)):
    ttl = payload.ttl_seconds or spec["default_ttl_seconds"]
    link = Link(
        code="",
        target_url=str(payload.target_url),
        expires_at=utcnow() + timedelta(seconds=ttl),
    )
    db.add(link)
    db.flush()
    link.code = encode_base62(link.id)
    db.commit()
    return LinkOut(
        code=link.code,
        short_url=f"{BASE_URL}/{link.code}",
        target_url=link.target_url,
        expires_at=link.expires_at,
    )


client = TestClient(app)
created = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][0], "ttl_seconds": 3600},
)
print("创建:", created.status_code)
print(created.json())

invalid = client.post("/links", json={"target_url": "not-a-url"})
print("非法地址:", invalid.status_code, invalid.json()["detail"][0]["msg"])

second = client.post("/links", json={"target_url": spec["sample_urls"][1]})
print("第二条:", second.status_code, second.json()["code"])
print("表内编号:", [row.id for row in SessionLocal().scalars(select(Link)).all()])

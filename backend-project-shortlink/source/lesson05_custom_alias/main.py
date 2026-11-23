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
import re

spec = json.loads(data_path("sample_urls.json").read_text(encoding="utf-8"))
ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
RESERVED = set(spec["reserved_aliases"])


def check_alias(alias: str) -> str:
    if alias in RESERVED:
        return "拒绝: 保留路径"
    if not ALIAS_RE.fullmatch(alias):
        return "拒绝: 格式不符"
    return "通过"


for alias in ("launch", "2026-report", "Docs", "api", "a" * 33, "-bad"):
    print(f"{alias:<12} {check_alias(alias)}")


from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException
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

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode_base62(number: int) -> str:
    if number <= 0:
        raise ValueError("编号必须为正整数")
    digits = []
    while number:
        number, remainder = divmod(number, 62)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


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
    custom_alias: str | None = Field(default=None, max_length=32)


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as session:
        yield session


def validate_alias(alias: str) -> None:
    if alias in RESERVED:
        raise HTTPException(
            status_code=422,
            detail={"code": "alias_reserved", "message": "该别名属于保留路径"},
        )
    if not ALIAS_RE.fullmatch(alias):
        raise HTTPException(
            status_code=422,
            detail={"code": "alias_invalid", "message": "别名格式不符合要求"},
        )


def unique_code(db: Session, link_id: int) -> str:
    candidate = encode_base62(link_id)
    exists = db.scalar(select(Link).where(Link.code == candidate))
    if exists is None:
        return candidate
    return f"{candidate}x{encode_base62(link_id)}"


app = FastAPI(title="短链接服务")


@app.post("/links", status_code=201)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)):
    ttl = spec["default_ttl_seconds"]
    if payload.custom_alias:
        validate_alias(payload.custom_alias)
        exists = db.scalar(select(Link).where(Link.code == payload.custom_alias))
        if exists is not None:
            raise HTTPException(
                status_code=409,
                detail={"code": "alias_taken", "message": "该别名已被占用"},
            )
        link = Link(
            code=payload.custom_alias,
            target_url=str(payload.target_url),
            expires_at=utcnow() + timedelta(seconds=ttl),
        )
        db.add(link)
        db.commit()
        return {"code": link.code, "custom": True}

    link = Link(
        code="",
        target_url=str(payload.target_url),
        expires_at=utcnow() + timedelta(seconds=ttl),
    )
    db.add(link)
    db.flush()
    link.code = unique_code(db, link.id)
    db.commit()
    return {"code": link.code, "custom": False}


client = TestClient(app)
custom = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][0], "custom_alias": "b"},
)
print("自定义别名:", custom.status_code, custom.json())

codes = []
for index in range(10):
    response = client.post(
        "/links",
        json={"target_url": f"https://example.com/page/{index}"},
    )
    codes.append(response.json()["code"])
print("自动编号:", codes)
print("第 11 号发生冲突后回退:", codes[-1])

duplicate = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][1], "custom_alias": "b"},
)
print("重复别名:", duplicate.status_code, duplicate.json())

reserved = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][1], "custom_alias": "api"},
)
print("保留别名:", reserved.status_code, reserved.json())


with SessionLocal() as session:
    rows = session.execute(
        select(Link.id, Link.code).order_by(Link.id).limit(6)
    ).all()
    for link_id, code in rows:
        print(f"id={link_id:<2} code={code}")

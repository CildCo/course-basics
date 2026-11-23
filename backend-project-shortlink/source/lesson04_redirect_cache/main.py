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
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
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


app = FastAPI(title="短链接服务")


@app.post("/links", status_code=201)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)):
    ttl = payload.ttl_seconds or spec["default_ttl_seconds"]
    link = Link(
        code="",
        target_url=str(payload.target_url),
        expires_at=utcnow() + timedelta(seconds=ttl),
    )
    db.add(link)
    db.flush()
    link.code = str(link.id)
    db.commit()
    return {"code": link.code, "target_url": link.target_url}


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="短链接不存在")
    max_age = spec["cache_max_age_seconds"]
    if link.expires_at is not None:
        remaining = int((link.expires_at - utcnow()).total_seconds())
        max_age = max(0, min(max_age, remaining))
    return RedirectResponse(
        url=link.target_url,
        status_code=302,
        headers={
            "Cache-Control": f"public, max-age={max_age}",
            "ETag": f'"{link.code}"',
        },
    )


client = TestClient(app)
created = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][0], "ttl_seconds": 3600},
)
code = created.json()["code"]
response = client.get(f"/{code}", follow_redirects=False)
print("状态码:", response.status_code)
print("Location:", response.headers["location"])
print("Cache-Control:", response.headers["cache-control"])
print("ETag:", response.headers["etag"])
print("响应体长度:", len(response.content))


short = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][1], "ttl_seconds": 90},
)
short_code = short.json()["code"]
short_response = client.get(f"/{short_code}", follow_redirects=False)
print("短有效期链接:", short_code, "->", short_response.headers["cache-control"])

missing = client.get("/missing", follow_redirects=False)
print("未知短码:", missing.status_code, missing.json())
print("未跟随跳转，目标地址没有被访问")

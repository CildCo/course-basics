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

from fastapi import Depends, FastAPI, HTTPException
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
    return {"code": link.code, "expires_at": link.expires_at.isoformat()}


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="短链接不存在")
    if link.expires_at is not None and link.expires_at <= utcnow():
        raise HTTPException(status_code=410, detail="短链接已过期")
    return RedirectResponse(url=link.target_url, status_code=302)


client = TestClient(app)
alive = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][0], "ttl_seconds": 3600},
)
expiring = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][1], "ttl_seconds": 60},
)
expiring_code = expiring.json()["code"]

with SessionLocal() as session:
    link = session.scalar(select(Link).where(Link.code == expiring_code))
    link.expires_at = utcnow() - timedelta(minutes=1)
    session.commit()

print("正常链接:", client.get(f"/{alive.json()['code']}", follow_redirects=False).status_code)
expired = client.get(f"/{expiring_code}", follow_redirects=False)
print("过期链接:", expired.status_code, expired.json())
print("未知链接:", client.get("/missing", follow_redirects=False).status_code)


from sqlalchemy import delete, func


@app.post("/maintenance/cleanup")
def cleanup(db: Session = Depends(get_db)):
    now = utcnow()
    expired_ids = select(Link.id).where(
        Link.expires_at.is_not(None),
        Link.expires_at <= now,
    )
    result = db.execute(delete(Link).where(Link.id.in_(expired_ids)))
    db.commit()
    return {"deleted": result.rowcount or 0}


with SessionLocal() as session:
    before = session.scalar(select(func.count()).select_from(Link))
print("清理前链接数:", before)

result = client.post("/maintenance/cleanup")
print("清理结果:", result.status_code, result.json())

with SessionLocal() as session:
    after = session.scalar(select(func.count()).select_from(Link))
print("清理后链接数:", after)
print("过期短码现在:", client.get(f"/{expiring_code}", follow_redirects=False).status_code)


class LinkCreateStrict(BaseModel):
    target_url: HttpUrl
    ttl_seconds: int | None = Field(default=None, ge=60, le=31_536_000)


for ttl in (30, 60, 31_536_001):
    try:
        LinkCreateStrict(target_url=spec["sample_urls"][0], ttl_seconds=ttl)
        print("接受 ttl:", ttl)
    except Exception as exc:
        print("拒绝 ttl:", ttl, "-", exc.errors()[0]["msg"])

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

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
from pydantic import BaseModel, HttpUrl
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
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
    visits: Mapped[int] = mapped_column(Integer, default=0)
    logs: Mapped[list["VisitLog"]] = relationship(back_populates="link")


class VisitLog(Base):
    __tablename__ = "visit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id"), index=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    client: Mapped[str] = mapped_column(String(64), default="anonymous")
    link: Mapped[Link] = relationship(back_populates="logs")


class LinkCreate(BaseModel):
    target_url: HttpUrl


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


def daily_series(db: Session, link_id: int, days: int = 7):
    today = utcnow().date()
    start = today - timedelta(days=days - 1)
    start_at = datetime.combine(start, datetime.min.time())
    rows = db.execute(
        select(func.date(VisitLog.visited_at), func.count())
        .where(
            VisitLog.link_id == link_id,
            VisitLog.visited_at >= start_at,
        )
        .group_by(func.date(VisitLog.visited_at))
    ).all()
    counts = {str(day): count for day, count in rows}
    labels = [start + timedelta(days=offset) for offset in range(days)]
    return [str(day) for day in labels], [counts.get(str(day), 0) for day in labels]


app = FastAPI(title="短链接服务")


@app.post("/links", status_code=201)
def create_link(payload: LinkCreate, db: Session = Depends(get_db)):
    link = Link(code="", target_url=str(payload.target_url))
    db.add(link)
    db.flush()
    link.code = str(link.id)
    db.commit()
    return {"code": link.code}


@app.get("/links/{code}/stats")
def stats(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="短链接不存在")
    labels, values = daily_series(db, link.id)
    return {
        "code": code,
        "total": sum(values),
        "visits": link.visits,
        "by_day": dict(zip(labels, values)),
    }


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(status_code=404, detail="短链接不存在")
    link.visits += 1
    db.add(VisitLog(link_id=link.id, client="demo"))
    db.commit()
    return RedirectResponse(url=link.target_url, status_code=302)


client = TestClient(app)
main_link = client.post("/links", json={"target_url": spec["sample_urls"][0]}).json()
other_link = client.post("/links", json={"target_url": spec["sample_urls"][1]}).json()

for _ in range(5):
    client.get(f"/{main_link['code']}", follow_redirects=False)
for _ in range(2):
    client.get(f"/{other_link['code']}", follow_redirects=False)

print("主链接统计:", client.get(f"/links/{main_link['code']}/stats").json())
print("另一条统计:", client.get(f"/links/{other_link['code']}/stats").json())


with SessionLocal() as db:
    link = db.scalar(select(Link).where(Link.code == main_link["code"]))
    now = utcnow()
    for offset, count in enumerate((3, 5, 2, 8, 4, 6), start=1):
        for _ in range(count):
            db.add(
                VisitLog(
                    link_id=link.id,
                    visited_at=now - timedelta(days=offset),
                    client="seed",
                )
            )
    db.commit()

with SessionLocal() as db:
    link = db.scalar(select(Link).where(Link.code == main_link["code"]))
    labels, values = daily_series(db, link.id)

for day, count in zip(labels, values):
    print(day, count)
print("7 天合计:", sum(values))


import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(labels, values, marker="o", color="#2f6f68", linewidth=2)
ax.fill_between(labels, values, color="#2f6f68", alpha=0.15)
ax.set_title("Daily visits in the last 7 days")
ax.set_xlabel("Day")
ax.set_ylabel("Visits")
ax.grid(axis="y", linestyle=":", alpha=0.5)
ax.set_ylim(bottom=0)
fig.autofmt_xdate()
plt.tight_layout()

chart = output_dir() / "visit-trend.png"
fig.savefig(chart, dpi=140, bbox_inches="tight")
print("图表文件:", chart.name, chart.stat().st_size, "字节")

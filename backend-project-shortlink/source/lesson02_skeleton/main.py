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

package = output_dir() / "skeleton_demo"
package.mkdir(parents=True, exist_ok=True)
(package / "__init__.py").write_text("", encoding="utf-8")

config_text = """from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str
    base_url: str
    default_ttl_seconds: int
    cache_max_age_seconds: int

    @classmethod
    def from_env(cls):
        return cls(
            database_url=os.getenv("SHORTLINK_DATABASE_URL", "sqlite:///./shortlink.db"),
            base_url=os.getenv("SHORTLINK_BASE_URL", "http://127.0.0.1:8010"),
            default_ttl_seconds=int(os.getenv("SHORTLINK_TTL", "604800")),
            cache_max_age_seconds=int(os.getenv("SHORTLINK_CACHE", "300")),
        )
"""
(package / "config.py").write_text(config_text, encoding="utf-8")

db_text = """from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def build_engine(url: str):
    if not url.startswith("sqlite"):
        return create_engine(url)
    options = {"connect_args": {"check_same_thread": False}}
    if url in {"sqlite://", "sqlite:///:memory:"}:
        options["poolclass"] = StaticPool
    return create_engine(url, **options)


def build_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
"""
(package / "db.py").write_text(db_text, encoding="utf-8")
print("生成:", ", ".join(sorted(path.name for path in package.iterdir())))


import os
import sys

root = str(output_dir())
if root not in sys.path:
    sys.path.insert(0, root)
for name in [
    item for item in sys.modules
    if item == "skeleton_demo" or item.startswith("skeleton_demo.")
]:
    del sys.modules[name]

from skeleton_demo.config import Settings

print("默认配置:", Settings.from_env())
os.environ["SHORTLINK_TTL"] = "3600"
os.environ["SHORTLINK_BASE_URL"] = "https://s.example.com"
print("环境覆盖:", Settings.from_env())


from fastapi import FastAPI
from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column
from fastapi.testclient import TestClient

from skeleton_demo.db import Base, build_engine, build_session_factory


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    target_url: Mapped[str] = mapped_column(String(512))


engine = build_engine("sqlite://")
Base.metadata.create_all(engine)
SessionLocal = build_session_factory(engine)

with SessionLocal() as session:
    session.add(Link(code="demo", target_url="https://example.com/docs"))
    session.commit()
    print("数据库行数:", len(session.scalars(select(Link)).all()))


def create_app() -> FastAPI:
    app = FastAPI(title="短链接服务")

    @app.get("/health")
    def health():
        with SessionLocal() as session:
            count = len(session.scalars(select(Link)).all())
        return {"status": "ok", "links": count}

    return app


client = TestClient(create_app())
response = client.get("/health")
print("健康检查:", response.status_code, response.json())
print("没有启动真实端口，请求由 TestClient 在进程内完成")

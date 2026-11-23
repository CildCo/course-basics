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


files = {}

files['shortlink/__init__.py'] = r"""from .main import create_app, get_db

__all__ = ["create_app", "get_db"]
"""

files['shortlink/database.py'] = r"""from sqlalchemy import create_engine, event
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
    engine = create_engine(url, **options)

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def build_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
"""

files['shortlink/models.py'] = r"""from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    target_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    visits: Mapped[int] = mapped_column(Integer, default=0)
    logs: Mapped[list["VisitLog"]] = relationship(
        back_populates="link", cascade="all, delete-orphan"
    )


class VisitLog(Base):
    __tablename__ = "visit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id"), index=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    client: Mapped[str] = mapped_column(String(64), default="anonymous")
    link: Mapped[Link] = relationship(back_populates="logs")
"""

files['shortlink/schemas.py'] = r"""from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class LinkCreate(BaseModel):
    target_url: HttpUrl
    custom_alias: str | None = Field(default=None, max_length=32)
    ttl_seconds: int | None = Field(default=None, ge=60, le=31_536_000)


class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str
    expires_at: datetime | None


class StatsOut(BaseModel):
    code: str
    total: int
    by_day: dict[str, int]
    last_visited_at: datetime | None
"""

files['shortlink/service.py'] = r"""import re
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import Link, VisitLog, utcnow
from .schemas import LinkCreate, StatsOut

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
RESERVED = {"admin", "api", "health", "links", "stats", "static"}


def encode_base62(number: int) -> str:
    if number <= 0:
        raise ValueError("编号必须为正整数")
    digits = []
    while number:
        number, remainder = divmod(number, 62)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


def validate_alias(alias: str) -> None:
    if alias in RESERVED:
        raise HTTPException(
            status_code=422,
            detail={"code": "alias_reserved", "message": "该别名属于保留路径"},
        )
    if not ALIAS_RE.fullmatch(alias):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "alias_invalid",
                "message": "别名需为 1-32 位小写字母、数字、下划线或短横线",
            },
        )


def _unique_code(session: Session, link_id: int) -> str:
    candidate = encode_base62(link_id)
    if session.scalar(select(Link).where(Link.code == candidate)) is None:
        return candidate
    return f"{candidate}x{encode_base62(link_id)}"


def create_link(
    session: Session,
    payload: LinkCreate,
    default_ttl_seconds: int,
    now: datetime | None = None,
) -> Link:
    now = now or utcnow()
    ttl = payload.ttl_seconds or default_ttl_seconds
    if payload.custom_alias:
        validate_alias(payload.custom_alias)
        exists = session.scalar(select(Link).where(Link.code == payload.custom_alias))
        if exists is not None:
            raise HTTPException(
                status_code=409,
                detail={"code": "alias_taken", "message": "该别名已被占用"},
            )
        link = Link(
            code=payload.custom_alias,
            target_url=str(payload.target_url),
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
        )
        session.add(link)
        session.commit()
        return link

    link = Link(
        code="",
        target_url=str(payload.target_url),
        created_at=now,
        expires_at=now + timedelta(seconds=ttl),
    )
    session.add(link)
    session.flush()
    link.code = _unique_code(session, link.id)
    session.commit()
    return link


def resolve_link(
    session: Session,
    code: str,
    client: str = "anonymous",
    now: datetime | None = None,
) -> Link:
    now = now or utcnow()
    link = session.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "link_not_found", "message": "短链接不存在"},
        )
    if link.expires_at is not None and link.expires_at <= now:
        raise HTTPException(
            status_code=410,
            detail={"code": "link_expired", "message": "短链接已过期"},
        )
    link.visits += 1
    session.add(VisitLog(link_id=link.id, visited_at=now, client=client))
    session.commit()
    return link


def cleanup_expired(session: Session, now: datetime | None = None) -> int:
    now = now or utcnow()
    expired_ids = select(Link.id).where(
        Link.expires_at.is_not(None), Link.expires_at <= now
    )
    session.execute(delete(VisitLog).where(VisitLog.link_id.in_(expired_ids)))
    result = session.execute(
        delete(Link).where(Link.expires_at.is_not(None), Link.expires_at <= now)
    )
    session.commit()
    return result.rowcount or 0


def link_stats(session: Session, code: str) -> StatsOut:
    link = session.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "link_not_found", "message": "短链接不存在"},
        )
    rows = session.execute(
        select(func.date(VisitLog.visited_at), func.count())
        .where(VisitLog.link_id == link.id)
        .group_by(func.date(VisitLog.visited_at))
        .order_by(func.date(VisitLog.visited_at))
    ).all()
    by_day = {str(day): count for day, count in rows}
    total = sum(by_day.values())
    last = session.scalar(
        select(func.max(VisitLog.visited_at)).where(VisitLog.link_id == link.id)
    )
    return StatsOut(code=code, total=total, by_day=by_day, last_visited_at=last)
"""

files['shortlink/main.py'] = r"""import os
from collections import defaultdict, deque
from time import monotonic

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import models  # noqa: F401 - 导入后建表才能找到模型
from .database import Base, build_engine, build_session_factory
from .models import utcnow
from .schemas import LinkCreate, LinkOut, StatsOut
from .service import cleanup_expired, create_link, link_stats, resolve_link


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = monotonic() if now is None else now
        events = self._events[key]
        while events and now - events[0] >= self.window_seconds:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True


def get_db(request: Request):
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


def to_link_out(link, base_url: str) -> LinkOut:
    return LinkOut(
        code=link.code,
        short_url=f"{base_url.rstrip('/')}/{link.code}",
        target_url=link.target_url,
        expires_at=link.expires_at,
    )


def create_app(
    *,
    database_url: str | None = None,
    base_url: str | None = None,
    default_ttl_seconds: int | None = None,
    cache_max_age_seconds: int | None = None,
    rate_limit: int = 5,
    rate_window_seconds: int = 60,
) -> FastAPI:
    database_url = database_url or os.getenv(
        "SHORTLINK_DATABASE_URL", "sqlite:///./shortlink.db"
    )
    base_url = base_url or os.getenv("SHORTLINK_BASE_URL", "http://127.0.0.1:8010")
    if default_ttl_seconds is None:
        default_ttl_seconds = int(os.getenv("SHORTLINK_TTL", "604800"))
    if cache_max_age_seconds is None:
        cache_max_age_seconds = int(os.getenv("SHORTLINK_CACHE", "300"))
    engine = build_engine(database_url)
    Base.metadata.create_all(engine)
    app = FastAPI(title="短链接服务")
    app.state.session_factory = build_session_factory(engine)
    app.state.limiter = RateLimiter(rate_limit, rate_window_seconds)

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            code = detail.get("code", "http_error")
            message = detail.get("message", "")
        else:
            code = "http_error"
            message = str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": message}},
            headers=exc.headers,
        )

    def check_rate_limit(
        request: Request,
        x_client_id: str = Header(default="anonymous"),
    ) -> None:
        key = f"{x_client_id}:{request.url.path}"
        if not app.state.limiter.allow(key):
            raise HTTPException(
                status_code=429,
                detail={"code": "rate_limited", "message": "请求过于频繁，请稍后再试"},
                headers={"Retry-After": str(rate_window_seconds)},
            )

    @app.get("/health")
    def health():
        return {"status": "ok", "base_url": base_url}

    @app.post("/links", status_code=201, response_model=LinkOut)
    def create(
        payload: LinkCreate,
        db: Session = Depends(get_db),
        _: None = Depends(check_rate_limit),
    ):
        link = create_link(db, payload, default_ttl_seconds)
        return to_link_out(link, base_url)

    @app.get("/links/{code}/stats", response_model=StatsOut)
    def stats(code: str, db: Session = Depends(get_db)):
        return link_stats(db, code)

    @app.post("/maintenance/cleanup")
    def cleanup(db: Session = Depends(get_db)):
        return {"deleted": cleanup_expired(db)}

    @app.get("/{code}")
    def redirect(code: str, request: Request, db: Session = Depends(get_db)):
        client = request.headers.get("X-Client-Id", "anonymous")
        link = resolve_link(db, code, client=client)
        max_age = cache_max_age_seconds
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

    return app
"""

files['tests/test_api.py'] = r"""import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from shortlink.database import Base, build_engine, build_session_factory
from shortlink.main import create_app, get_db
from shortlink.models import Link, utcnow


@pytest.fixture()
def session_factory(tmp_path):
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return build_session_factory(engine)


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        with session_factory() as session:
            yield session

    app = create_app(database_url="sqlite://", rate_limit=3)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def test_create_and_redirect(client):
    created = client.post(
        "/links",
        json={"target_url": "https://example.com/docs", "ttl_seconds": 3600},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["short_url"].endswith("/" + body["code"])
    response = client.get(f"/{body['code']}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/docs"
    assert "max-age=" in response.headers["cache-control"]


def test_alias_conflict(client):
    first = client.post(
        "/links",
        json={"target_url": "https://example.com/a", "custom_alias": "docs"},
    )
    assert first.status_code == 201
    second = client.post(
        "/links",
        json={"target_url": "https://example.com/b", "custom_alias": "docs"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "alias_taken"


def test_reserved_alias(client):
    response = client.post(
        "/links",
        json={"target_url": "https://example.com/a", "custom_alias": "api"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "alias_reserved"


def test_expired_link_and_cleanup(client, session_factory):
    created = client.post(
        "/links",
        json={"target_url": "https://example.com/old", "ttl_seconds": 60},
    )
    code = created.json()["code"]
    with session_factory() as session:
        link = session.scalar(select(Link).where(Link.code == code))
        link.expires_at = utcnow().replace(year=2020)
        session.commit()
    assert client.get(f"/{code}", follow_redirects=False).status_code == 410
    deleted = client.post("/maintenance/cleanup")
    assert deleted.json()["deleted"] == 1
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404


def test_stats(client):
    created = client.post(
        "/links",
        json={"target_url": "https://example.com/stats"},
    )
    code = created.json()["code"]
    for _ in range(3):
        client.get(f"/{code}", follow_redirects=False)
    stats = client.get(f"/links/{code}/stats").json()
    assert stats["total"] == 3
    assert sum(stats["by_day"].values()) == 3


def test_rate_limit(client):
    payload = {"target_url": "https://example.com/limited"}
    statuses = [
        client.post(
            "/links",
            json=payload,
            headers={"X-Client-Id": "tester"},
        ).status_code
        for _ in range(4)
    ]
    assert statuses[:3] == [201, 201, 201]
    assert statuses[3] == 429
"""

files['README.md'] = r"""# 短链接服务

基于 FastAPI、SQLAlchemy 和 SQLite 的短链接服务，支持自动短码、自定义别名、过期清理、访问统计和内存限流。

## 启动

pip install -r requirements.txt
uvicorn shortlink.main:create_app --factory --host 127.0.0.1 --port 8010

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | /health | 健康检查 |
| POST | /links | 创建短链接 |
| GET | /{code} | 302 跳转 |
| GET | /links/{code}/stats | 访问统计 |
| POST | /maintenance/cleanup | 清理过期链接 |

## 配置

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| SHORTLINK_DATABASE_URL | sqlite:///./shortlink.db | 数据库连接 |
| SHORTLINK_BASE_URL | http://127.0.0.1:8010 | 短链接域名 |
| SHORTLINK_TTL | 604800 | 默认有效期秒数 |
| SHORTLINK_CACHE | 300 | 最大缓存秒数 |

## 测试

pytest -q
"""

files['deploy.md'] = r"""# 上线前检查

| 项目 | 要求 | 本次演练 |
| --- | --- | --- |
| 数据库 | 文件可写，或换成 PostgreSQL | SQLite 文件 |
| 迁移 | 发布前执行建表脚本 | create_all |
| 域名 | 短链接域名可公网访问 | 本地地址 |
| 缓存 | 反向代理尊重 Cache-Control | 已返回 |
| 限流 | 多实例时换成共享存储 | 进程内队列 |
| 监控 | 健康检查和错误日志接入 | /health |
| 备份 | 数据库按日备份 | 待接入 |
| 清理 | 定时任务调用清理接口 | 手动演练 |
"""

files['requirements.txt'] = r"""fastapi>=0.110
uvicorn[standard]>=0.27
sqlalchemy>=2.0
pydantic>=2.6
httpx>=0.27
pytest>=8.0
"""

root = output_dir() / "shortlink_project"
for relative, text in files.items():
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

print("写入", len(files), "个文件到", root.name)
for path in sorted(root.rglob("*")):
    if path.is_file() and ".pytest_cache" not in path.parts and "__pycache__" not in path.parts:
        print(" ", path.relative_to(root).as_posix())


import sys

from sqlalchemy import select

root_str = str(root)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
for name in [
    item for item in sys.modules
    if item == "shortlink" or item.startswith("shortlink.")
]:
    del sys.modules[name]

from fastapi.testclient import TestClient
from shortlink.main import create_app
from shortlink.models import Link, utcnow

import json

spec = json.loads(data_path("sample_urls.json").read_text(encoding="utf-8"))
database_file = output_dir() / "rehearsal.db"
if database_file.exists():
    database_file.unlink()

app = create_app(
    database_url=f"sqlite:///{database_file.as_posix()}",
    base_url="https://s.example.com",
    rate_limit=5,
)
client = TestClient(app)

health = client.get("/health")
print("健康检查:", health.status_code, health.json())

created = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][0], "ttl_seconds": 3600},
)
print("创建:", created.status_code, created.json())
code = created.json()["code"]

alias = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][1], "custom_alias": "launch"},
)
print("别名:", alias.status_code, alias.json()["short_url"])

redirect = client.get(f"/{code}", follow_redirects=False)
print("跳转:", redirect.status_code, redirect.headers["location"], redirect.headers["cache-control"])
client.get(f"/{code}", follow_redirects=False)
print("统计:", client.get(f"/links/{code}/stats").json())

duplicate = client.post(
    "/links",
    json={"target_url": spec["sample_urls"][2], "custom_alias": "launch"},
)
print("重复别名:", duplicate.status_code, duplicate.json()["error"]["code"])

statuses = [
    client.post(
        "/links",
        json={"target_url": f"https://example.com/load/{index}"},
        headers={"X-Client-Id": "load-test"},
    ).status_code
    for index in range(6)
]
print("同一客户端连续创建:", statuses)

expired = client.post(
    "/links",
    json={"target_url": "https://example.com/old", "ttl_seconds": 60},
)
expired_code = expired.json()["code"]
with app.state.session_factory() as session:
    link = session.scalar(select(Link).where(Link.code == expired_code))
    link.expires_at = utcnow().replace(year=2020)
    session.commit()
print("过期访问:", client.get(f"/{expired_code}", follow_redirects=False).status_code)
print("清理:", client.post("/maintenance/cleanup").json())
print("清理后:", client.get(f"/{expired_code}", follow_redirects=False).status_code)


import os
import subprocess

environment = dict(os.environ)
environment["PYTHONIOENCODING"] = "utf-8"
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--color=no",
        "-p",
        "no:cacheprovider",
        "tests/test_api.py",
    ],
    cwd=root,
    env=environment,
    capture_output=True,
    text=True,
)
print(result.stdout.strip())
if result.stderr.strip():
    print(result.stderr.strip())
print("退出码:", result.returncode)
assert result.returncode == 0

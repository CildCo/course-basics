from pathlib import Path


def course_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for base in (here, *here.parents):
        if (base / "assets").is_dir() and (
            (base / "collection.json").exists() or (base / "README.md").exists()
        ):
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

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict
from sqlalchemy import String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(20))
    views: Mapped[int] = mapped_column(default=0)


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    views: int


class Page(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    size: int
    pages: int


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

with Session(engine) as session:
    session.add_all(
        [
            Article(title="FastAPI 分层实践", category="backend", views=320),
            Article(title="SQLAlchemy 会话管理", category="backend", views=280),
            Article(title="Pytest 夹具入门", category="testing", views=190),
            Article(title="JWT 过期处理", category="backend", views=410),
            Article(title="分页参数设计", category="api", views=150),
            Article(title="统一错误响应", category="api", views=230),
            Article(title="依赖覆盖技巧", category="testing", views=170),
        ]
    )
    session.commit()

with Session(engine) as session:
    print("文章数据:", session.scalar(select(func.count()).select_from(Article)))


def build_app() -> FastAPI:
    app = FastAPI(title="分页与错误")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": str(exc.detail)}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request, exc):
        fields = [
            {
                "field": ".".join(str(part) for part in error["loc"]),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "参数不合法",
                    "fields": fields,
                }
            },
        )

    @app.get("/articles", response_model=Page)
    def list_articles(
        page: int = Query(1, ge=1),
        size: int = Query(3, ge=1, le=20),
        q: str | None = Query(None, min_length=1, max_length=30),
        category: str | None = Query(None),
        sort: str = Query("id"),
    ):
        sort_columns = {
            "id": Article.id,
            "views": Article.views.desc(),
            "title": Article.title,
        }
        if sort not in sort_columns:
            raise HTTPException(status_code=400, detail="sort 只支持 id、views、title")

        conditions = []
        if q:
            conditions.append(Article.title.contains(q))
        if category:
            conditions.append(Article.category == category)

        statement = select(Article)
        count_statement = select(func.count()).select_from(Article)
        for condition in conditions:
            statement = statement.where(condition)
            count_statement = count_statement.where(condition)

        with SessionLocal() as session:
            total = session.scalar(count_statement) or 0
            rows = session.scalars(
                statement.order_by(sort_columns[sort], Article.id)
                .offset((page - 1) * size)
                .limit(size)
            ).all()
            items = [ArticleOut.model_validate(row) for row in rows]
            pages = (total + size - 1) // size
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
            }

    @app.get("/articles/{article_id}", response_model=ArticleOut)
    def get_article(article_id: int):
        with SessionLocal() as session:
            row = session.get(Article, article_id)
            if row is None:
                raise HTTPException(status_code=404, detail="文章不存在")
            return ArticleOut.model_validate(row)

    return app


app = build_app()
client = TestClient(app)
print("分页应用已就绪")


first = client.get("/articles")
summary = {key: first.json()[key] for key in ("total", "page", "size", "pages")}
print("默认第一页:", first.status_code, summary)
print("标题:", [item["title"] for item in first.json()["items"]])

second = client.get("/articles", params={"page": 2, "size": 3})
print("第二页:", [item["title"] for item in second.json()["items"]])

filtered = client.get("/articles", params={"category": "backend", "sort": "views"})
print("后端分类按热度:", [(item["title"], item["views"]) for item in filtered.json()["items"]])

searched = client.get("/articles", params={"q": "错误"})
print("关键词搜索:", [item["title"] for item in searched.json()["items"]])


bad_size = client.get("/articles", params={"size": 100})
print("size 超限:", bad_size.status_code, bad_size.json())

bad_sort = client.get("/articles", params={"sort": "owner"})
print("非法排序:", bad_sort.status_code, bad_sort.json())

missing = client.get("/articles/999")
print("文章不存在:", missing.status_code, missing.json())

missing_route = client.get("/not-found")
print("未知路径:", missing_route.status_code, missing_route.json())

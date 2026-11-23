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

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)


class TodoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=60, description="待办标题")
    priority: int = Field(default=2, ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("tags")
    @classmethod
    def dedupe_tags(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def check_urgent(self) -> "TodoCreate":
        if "紧急" in self.tags and self.priority < 4:
            raise ValueError("带“紧急”标签时优先级至少为 4")
        return self


payload = TodoCreate(title="  补接口文档  ", priority=4, tags=["后端", "后端", "紧急"])
print("清洗后:", payload.model_dump())
print("JSON:", payload.model_dump_json())


bad_inputs = [
    {"title": "", "priority": 9},
    {"title": "值班", "tags": ["紧急"], "priority": 2},
]

for data in bad_inputs:
    try:
        TodoCreate(**data)
    except ValidationError as exc:
        for error in exc.errors():
            location = error["loc"] or ("model",)
            print("字段:", location, "| 类型:", error["type"], "| 提示:", error["msg"])
    print("-" * 40)


from types import SimpleNamespace


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: int
    tags: list[str] = Field(default_factory=list)
    owner_id: int = Field(exclude=True)

    @computed_field
    @property
    def label(self) -> str:
        return f"[{self.priority}] {self.title}"


row = SimpleNamespace(id=7, title="补接口文档", priority=4, tags=["后端"], owner_id=42)
out = TodoRead.model_validate(row)
print("模型序列化:", out.model_dump())
print("响应 JSON:", out.model_dump_json())


from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()


@app.post("/todos", response_model=TodoRead, status_code=201)
def create_todo(payload: TodoCreate):
    return SimpleNamespace(
        id=1,
        title=payload.title,
        priority=payload.priority,
        tags=payload.tags,
        owner_id=42,
    )


client = TestClient(app)
created = client.post(
    "/todos",
    json={"title": "补接口文档", "priority": 4, "tags": ["后端", "后端"]},
)
print("创建:", created.status_code, created.json())

invalid = client.post("/todos", json={"title": "", "priority": 9})
print("非法输入:", invalid.status_code)
for item in invalid.json()["detail"]:
    print(item["loc"], item["msg"])

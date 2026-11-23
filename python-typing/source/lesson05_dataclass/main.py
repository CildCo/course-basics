from dataclasses import dataclass, field


@dataclass
class Lesson:
    id: str
    title: str
    minutes: int = 15
    tags: list[str] = field(default_factory=list)


lesson = Lesson("01", "为什么需要类型注解", tags=["typing"])
print(lesson)
print("标签：", lesson.tags)


@dataclass(frozen=True)
class Point:
    x: int
    y: int


point = Point(1, 2)
print(point)
print("相等：", point == Point(1, 2))

try:
    point.x = 9
except Exception as exc:
    print(type(exc).__name__, exc)


from typing import TypedDict


class Article(TypedDict):
    title: str
    views: int
    tags: list[str]


article: Article = {"title": "类型注解入门", "views": 120, "tags": ["python"]}
print(article)
print("运行时类型：", type(article).__name__)


from typing import Final, Literal

Status = Literal["draft", "published", "archived"]


def describe_status(status: Status) -> str:
    return f"当前状态：{status}"


MAX_LESSONS: Final = 6

print(describe_status("published"))
print("课程上限：", MAX_LESSONS)

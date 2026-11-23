def total(scores: list[int]) -> int:
    return sum(scores)

def group_names(names: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for name in names:
        groups.setdefault(name[0].upper(), []).append(name)
    return groups

print(total([80, 90, 75]))
print(group_names(["alice", "bob", "anna"]))


def min_max(values: list[int]) -> tuple[int, int]:
    return min(values), max(values)

def unique_tags(tags: list[str]) -> set[str]:
    return {tag.strip().lower() for tag in tags}

print(min_max([4, 1, 9, 2]))
print(sorted(unique_tags(["Python", " python", "Stdlib"])))


from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

print(first([10, 20, 30]))
print(first(["a", "b"]))
print("注解：", first.__annotations__)


from typing import Callable, Generic

U = TypeVar("U")

class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

    def map(self, func: Callable[[T], U]) -> "Box[U]":
        return Box(func(self.value))

number_box = Box(21)
text_box = number_box.map(lambda n: f"box-{n}")
print(number_box.get())
print(text_box.get())

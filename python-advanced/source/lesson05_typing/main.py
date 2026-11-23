def greet(name: str, times: int = 1) -> str:
    return ("你好，" + name + "！") * times

print(greet("小居", 2))


from typing import Optional

def find_score(name: str, scores: dict[str, int]) -> Optional[int]:
    return scores.get(name)

print(find_score("小居", {"小居": 88}))
print(find_score("小明", {"小居": 88}))


from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

point = Point(2, 5)
print(point)
print(point.x + point.y)


from dataclasses import dataclass, field

@dataclass
class Team:
    name: str
    members: list[str] = field(default_factory=list)

team = Team("码袋子")
team.members.append("小居")
print(team)

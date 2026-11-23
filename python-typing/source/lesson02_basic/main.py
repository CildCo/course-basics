def price_with_tax(price: float, rate: float = 0.06) -> float:
    return round(price * (1 + rate), 2)

print(price_with_tax(100))
print(price_with_tax(100, 0.1))
print(price_with_tax.__annotations__)


from typing import Optional

def find_user(user_id: int) -> Optional[str]:
    users = {1: "alice", 2: "bob"}
    return users.get(user_id)

print(find_user(1))
print(find_user(9))
print("返回注解：", find_user.__annotations__["return"])


from typing import Union

def format_value(value: Union[int, float]) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)

print(format_value(3))
print(format_value(3.14159))
print("参数注解：", format_value.__annotations__["value"])


def parse_score(raw: str) -> int | None:
    return int(raw) if raw.isdigit() else None

print(parse_score("88"))
print(parse_score("缺考"))
print("返回注解：", parse_score.__annotations__["return"])

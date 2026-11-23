import math

print(math.sqrt(16))
print(round(math.pi, 2))


from datetime import date, timedelta

start = date(2026, 10, 24)
end = start + timedelta(days=7)
print("开始：", start)
print("七天后：", end)


import random

random.seed(7)
print(random.randint(1, 100))
print(random.choice(["石头", "剪刀", "布"]))


from pathlib import Path

path = Path("data/report.csv")
print(path.name)
print(path.suffix)
print(path.parent)

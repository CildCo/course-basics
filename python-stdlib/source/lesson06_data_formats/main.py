import json
import tempfile
from pathlib import Path

tmp = tempfile.TemporaryDirectory()
root = Path(tmp.name)

data = {"course": "Python 标准库实战", "lessons": 10, "tags": ["python", "stdlib"]}
json_path = root / "course.json"
json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(json_path.read_text(encoding="utf-8"))

loaded = json.loads(json_path.read_text(encoding="utf-8"))
print("类型：", type(loaded).__name__, "课次：", loaded["lessons"])


import csv

rows = [
    {"day": "周一", "topic": "容器", "minutes": 14},
    {"day": "周二", "topic": "迭代", "minutes": 16},
    {"day": "周三", "topic": "函数工具", "minutes": 15},
]
csv_path = root / "plan.csv"

with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["day", "topic", "minutes"])
    writer.writeheader()
    writer.writerows(rows)

with csv_path.open(encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle):
        print(row["day"], row["topic"], row["minutes"])


import pickle
from datetime import date

record = {
    "title": "第 6 课",
    "tags": ("json", "csv", "pickle"),
    "day": date(2026, 3, 6),
}
pickle_path = root / "record.pkl"
pickle_path.write_bytes(pickle.dumps(record))

restored = pickle.loads(pickle_path.read_bytes())
print(restored)
print("tags 类型：", type(restored["tags"]).__name__)
print("day 类型：", type(restored["day"]).__name__)

records = [
    {"item": "早餐", "amount": 12.5, "category": "餐饮"},
    {"item": "地铁", "amount": 4.0, "category": "交通"},
]
print(records[0])
print(len(records))


def add_record(records, item, amount, category):
    records.append({"item": item, "amount": amount, "category": category})
    return records

add_record(records, "咖啡", 18.0, "餐饮")
print("记录数：", len(records))


def total(records):
    return sum(record["amount"] for record in records)

def summary(records):
    lines = []
    for record in records:
        lines.append(f'{record["category"]} / {record["item"]}: {record["amount"]} 元')
    lines.append(f"合计: {total(records)} 元")
    return "\n".join(lines)

print(summary(records))


import json
from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
path = output / "records.json"
path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
loaded = json.loads(path.read_text(encoding="utf-8"))
print("读回记录数：", len(loaded))
print(summary(loaded))

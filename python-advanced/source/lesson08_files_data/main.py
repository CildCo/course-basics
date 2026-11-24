from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
path = output / "report.txt"
path.write_text("第一行\n第二行\n", encoding="utf-8")
print(path.name)
print(path.suffix)
print(path.exists())
print(path.read_text(encoding="utf-8"))


import json

data = {"name": "小李", "days": 3, "topics": ["变量", "列表"]}
json_path = output / "data.json"
json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
loaded = json.loads(json_path.read_text(encoding="utf-8"))
print(loaded["topics"])


import csv

csv_path = output / "scores.csv"
with csv_path.open("w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["name", "score"])
    writer.writerow(["小李", 88])
    writer.writerow(["小明", 95])

with csv_path.open(encoding="utf-8", newline="") as file:
    for row in csv.DictReader(file):
        print(row["name"], row["score"])


files = sorted(path.name for path in output.glob("*.csv"))
print(files)

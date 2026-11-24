from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
path = output / "demo.txt"
path.write_text("第一行\n第二行\n", encoding="utf-8")
print(path.read_text(encoding="utf-8"))


with path.open(encoding="utf-8") as file:
    for line in file:
        print(line.strip())


with path.open("a", encoding="utf-8") as file:
    file.write("第三行\n")

print(path.read_text(encoding="utf-8"))


import json

data = {"name": "小李", "days": 3, "topics": ["变量", "列表"]}
json_path = output / "demo.json"
json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
loaded = json.loads(json_path.read_text(encoding="utf-8"))
print(loaded["topics"])

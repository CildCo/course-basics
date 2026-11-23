from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
path = output / "demo.txt"

with path.open("w", encoding="utf-8") as file:
    file.write("第一行\n")

print(path.read_text(encoding="utf-8"))


class Step:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print(f"进入 {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb):
        print(f"离开 {self.name}")
        return False

with Step("数据库"):
    print("处理数据")


from contextlib import contextmanager

@contextmanager
def step(name):
    print(f"开始 {name}")
    try:
        yield name
    finally:
        print(f"结束 {name}")

with step("任务") as current:
    print("执行", current)

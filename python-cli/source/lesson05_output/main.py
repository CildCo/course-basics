import csv
import io
import json
import unicodedata
from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


TASKS = json.loads(data_path("tasks.json").read_text(encoding="utf-8"))
COLUMNS = [
    ("id", "编号"),
    ("title", "标题"),
    ("priority", "优先级"),
    ("done", "状态"),
]


def cell_text(task, key):
    if key == "done":
        return "完成" if task["done"] else "待办"
    return str(task[key])


if __name__ == "__main__":
    print("字段：", [label for _, label in COLUMNS])
    print("第一条：", [cell_text(TASKS[0], key) for key, _ in COLUMNS])


def display_width(text):
    return sum(
        2 if unicodedata.east_asian_width(char) in "WF" else 1
        for char in text
    )


def pad(text, width):
    return text + " " * (width - display_width(text))


def render_table(tasks):
    headers = [label for _, label in COLUMNS]
    rows = [[cell_text(task, key) for key, _ in COLUMNS] for task in tasks]
    widths = [
        max(display_width(header), *(display_width(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    def line(values):
        return " | ".join(pad(value, width) for value, width in zip(values, widths))

    separator = "-+-".join("-" * width for width in widths)
    body = [line(row) for row in rows]
    return "\n".join([line(headers), separator, *body])


if __name__ == "__main__":
    print(render_table(TASKS))


def render_json(tasks):
    return json.dumps(tasks, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print(render_json(TASKS))


def render_csv(tasks):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([label for _, label in COLUMNS])
    for task in tasks:
        writer.writerow([cell_text(task, key) for key, _ in COLUMNS])
    return buffer.getvalue()


OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)
CSV_PATH = OUTPUT / "tasks.csv"

if __name__ == "__main__":
    text = render_csv(TASKS)
    print(text, end="")
    CSV_PATH.write_text(text, encoding="utf-8-sig", newline="")
    print()
    print("已写入：", CSV_PATH.relative_to(Path.cwd()))


def render(tasks, fmt):
    renderers = {"table": render_table, "json": render_json, "csv": render_csv}
    try:
        renderer = renderers[fmt]
    except KeyError as exc:
        raise ValueError(f"不支持的格式：{fmt}") from exc
    return renderer(tasks)


if __name__ == "__main__":
    for fmt in ("table", "json", "csv"):
        text = render(TASKS[:2], fmt)
        print(f"[{fmt}] 前 60 个字符：{text[:60]!r}")


import shutil

if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("临时文件已清理：", not CSV_PATH.exists())

import shutil
from pathlib import Path

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)


def write_module(name: str, source: str) -> Path:
    path = output_dir / name
    path.write_text(source, encoding="utf-8")
    return path


TYPED_APP = """from dataclasses import dataclass


@dataclass
class Task:
    title: str
    done: bool = False


def complete(task: Task) -> Task:
    return Task(title=task.title, done=True)


def count_done(tasks: list[Task]) -> int:
    return sum(1 for task in tasks if task.done)"""
write_module("typed_app.py", TYPED_APP)
print("已写入 output/typed_app.py")


BROKEN_APP = """def double(value: int) -> int:
    return value * 2


result: str = double(21)"""

LINT_ME = """import json


def greet(name):
    return "hi " + nmae"""

write_module("broken_app.py", BROKEN_APP)
write_module("lint_me.py", LINT_ME)
print("已写入 broken_app.py 和 lint_me.py")


import subprocess
import sys


def run(command: list[str]) -> int:
    print("$", " ".join(command))
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "").strip()
    if output:
        print(output)
    if result.stderr.strip():
        print(result.stderr.strip())
    print("退出码：", result.returncode)
    print()
    return result.returncode


mypy_ok = run([
    sys.executable, "-m", "mypy",
    "--cache-dir", "output/.mypy_cache",
    "output/typed_app.py",
])
assert mypy_ok == 0


mypy_broken = run([
    sys.executable, "-m", "mypy",
    "--cache-dir", "output/.mypy_cache",
    "output/broken_app.py",
])
assert mypy_broken == 1


ruff_broken = run([
    sys.executable, "-m", "ruff", "check",
    "--isolated", "--no-cache", "--select", "F",
    "--output-format=concise",
    "output/lint_me.py",
])
assert ruff_broken == 1


FIXED_APP = """def double(value: int) -> int:
    return value * 2


result: int = double(21)
print(result)"""

FIXED_LINT = """def greet(name: str) -> str:
    return "hi " + name"""

write_module("fixed_app.py", FIXED_APP)
write_module("fixed_lint.py", FIXED_LINT)

mypy_fixed = run([
    sys.executable, "-m", "mypy",
    "--cache-dir", "output/.mypy_cache",
    "output/fixed_app.py",
])
ruff_fixed = run([
    sys.executable, "-m", "ruff", "check",
    "--isolated", "--no-cache", "--select", "F",
    "--output-format=concise",
    "output/fixed_lint.py",
])
assert mypy_fixed == 0 and ruff_fixed == 0

shutil.rmtree(output_dir, ignore_errors=True)
print("检查完成，已清理 output/")

"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_why/main.py",
    "lesson02_strategy/main.py",
    "lesson03_factory/main.py",
    "lesson04_adapter/main.py",
    "lesson05_observer/main.py",
    "lesson06_decorator/main.py",
    "lesson07_repository/main.py",
    "lesson08_refactor/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

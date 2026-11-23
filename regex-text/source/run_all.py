"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_basics/main.py",
    "lesson02_groups/main.py",
    "lesson03_patterns/main.py",
    "lesson04_re/main.py",
    "lesson05_performance/main.py",
    "lesson06_extract/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

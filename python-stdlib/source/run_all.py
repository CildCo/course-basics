"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_collections/main.py",
    "lesson02_itertools/main.py",
    "lesson03_functools/main.py",
    "lesson04_datetime/main.py",
    "lesson05_pathlib/main.py",
    "lesson06_data_formats/main.py",
    "lesson07_text/main.py",
    "lesson08_stats_random/main.py",
    "lesson09_subprocess/main.py",
    "lesson10_tool/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_series/main.py",
    "lesson02_read_csv/main.py",
    "lesson03_select/main.py",
    "lesson04_filter_sort/main.py",
    "lesson05_columns/main.py",
    "lesson06_missing/main.py",
    "lesson07_groupby/main.py",
    "lesson08_merge/main.py",
    "lesson09_pivot/main.py",
    "lesson10_datetime/main.py",
    "lesson11_plot/main.py",
    "lesson12_analysis/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

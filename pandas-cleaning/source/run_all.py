"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_inspect/main.py",
    "lesson02_schema/main.py",
    "lesson03_missing/main.py",
    "lesson04_duplicates/main.py",
    "lesson05_strings/main.py",
    "lesson06_dates/main.py",
    "lesson07_outliers/main.py",
    "lesson08_validate/main.py",
    "lesson09_pipeline/main.py",
    "lesson10_report/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

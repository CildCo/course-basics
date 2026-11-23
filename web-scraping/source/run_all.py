"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_http/main.py",
    "lesson02_requests/main.py",
    "lesson03_bs4/main.py",
    "lesson04_selectors/main.py",
    "lesson05_pagination/main.py",
    "lesson06_politeness/main.py",
    "lesson07_clean_save/main.py",
    "lesson08_project/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

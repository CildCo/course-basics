"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_hello/main.py",
    "lesson02_variables/main.py",
    "lesson03_control/main.py",
    "lesson04_functions/main.py",
    "lesson05_collections/main.py",
    "lesson06_errors/main.py",
    "lesson07_modules/main.py",
    "lesson08_files/main.py",
    "lesson09_strings/main.py",
    "lesson10_classes/main.py",
    "lesson11_wordcount/main.py",
    "lesson12_project/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

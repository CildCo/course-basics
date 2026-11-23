"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_comprehensions/main.py",
    "lesson02_generators/main.py",
    "lesson03_decorators/main.py",
    "lesson04_context/main.py",
    "lesson05_typing/main.py",
    "lesson06_errors_logging/main.py",
    "lesson07_modules/main.py",
    "lesson08_files_data/main.py",
    "lesson09_concurrency/main.py",
    "lesson10_cli_tool/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

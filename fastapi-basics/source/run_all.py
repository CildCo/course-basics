"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_routes/main.py",
    "lesson02_models/main.py",
    "lesson03_params/main.py",
    "lesson04_errors/main.py",
    "lesson05_dependencies/main.py",
    "lesson06_database/main.py",
    "lesson07_pagination/main.py",
    "lesson08_auth/main.py",
    "lesson09_testing/main.py",
    "lesson10_project/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

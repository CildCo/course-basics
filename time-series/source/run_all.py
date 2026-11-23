"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_concepts/main.py",
    "lesson02_index/main.py",
    "lesson03_trend/main.py",
    "lesson04_seasonality/main.py",
    "lesson05_lag/main.py",
    "lesson06_baseline/main.py",
    "lesson07_regression/main.py",
    "lesson08_project/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

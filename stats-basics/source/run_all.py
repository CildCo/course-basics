"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_descriptive/main.py",
    "lesson02_spread/main.py",
    "lesson03_correlation/main.py",
    "lesson04_sampling/main.py",
    "lesson05_hypothesis/main.py",
    "lesson06_ab_test/main.py",
    "lesson07_scipy/main.py",
    "lesson08_report/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

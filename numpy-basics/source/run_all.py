"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_arrays/main.py",
    "lesson02_shape/main.py",
    "lesson03_indexing/main.py",
    "lesson04_reshape/main.py",
    "lesson05_broadcasting/main.py",
    "lesson06_ufunc/main.py",
    "lesson07_aggregation/main.py",
    "lesson08_random/main.py",
    "lesson09_save_vectorize/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

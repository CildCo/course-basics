"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_pixels/main.py",
    "lesson02_pil_basic/main.py",
    "lesson03_filters/main.py",
    "lesson04_histogram/main.py",
    "lesson05_edges/main.py",
    "lesson06_transform/main.py",
    "lesson07_batch/main.py",
    "lesson08_project/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

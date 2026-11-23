"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_dataset/main.py",
    "lesson02_rank/main.py",
    "lesson03_window_agg/main.py",
    "lesson04_cte/main.py",
    "lesson05_index/main.py",
    "lesson06_explain/main.py",
    "lesson07_transaction/main.py",
    "lesson08_design/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

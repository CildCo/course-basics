"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_naming/main.py",
    "lesson02_duplication/main.py",
    "lesson03_branches/main.py",
    "lesson04_side_effects/main.py",
    "lesson05_errors/main.py",
    "lesson06_extract/main.py",
    "lesson07_policy/main.py",
    "lesson08_review/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

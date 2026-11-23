"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_source_bytecode/main.py",
    "lesson02_memory/main.py",
    "lesson03_encoding/main.py",
    "lesson04_process/main.py",
    "lesson05_filesystem/main.py",
    "lesson06_network/main.py",
    "lesson07_index/main.py",
    "lesson08_deploy/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

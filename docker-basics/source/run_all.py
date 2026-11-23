"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_images/main.py",
    "lesson02_first_container/main.py",
    "lesson03_dockerfile/main.py",
    "lesson04_port_volume/main.py",
    "lesson05_compose/main.py",
    "lesson06_logs_cleanup/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

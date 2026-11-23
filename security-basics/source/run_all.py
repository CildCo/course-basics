"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_password/main.py",
    "lesson02_secrets/main.py",
    "lesson03_injection/main.py",
    "lesson04_https/main.py",
    "lesson05_dependencies/main.py",
    "lesson06_logging/main.py",
    "lesson07_backup/main.py",
    "lesson08_privacy/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

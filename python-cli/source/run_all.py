"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_argparse/main.py",
    "lesson02_click/main.py",
    "lesson03_subcommands/main.py",
    "lesson04_config_logging/main.py",
    "lesson05_output/main.py",
    "lesson06_package/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

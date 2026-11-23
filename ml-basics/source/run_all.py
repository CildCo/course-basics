"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_problem/main.py",
    "lesson02_split_baseline/main.py",
    "lesson03_preprocess/main.py",
    "lesson04_regression/main.py",
    "lesson05_classification/main.py",
    "lesson06_metrics/main.py",
    "lesson07_overfitting/main.py",
    "lesson08_cross_validation/main.py",
    "lesson09_pipeline_save/main.py",
    "lesson10_project/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

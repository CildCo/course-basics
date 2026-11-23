"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_workbook/main.py",
    "lesson02_pandas_excel/main.py",
    "lesson03_openpyxl/main.py",
    "lesson04_styles/main.py",
    "lesson05_formula_chart/main.py",
    "lesson06_merge/main.py",
    "lesson07_split/main.py",
    "lesson08_report/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

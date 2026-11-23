"""运行全部课次，任何一课失败立即退出。"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_docx_structure/main.py",
    "lesson02_docx_read_write/main.py",
    "lesson03_template/main.py",
    "lesson04_pdf_extract/main.py",
    "lesson05_pdf_merge/main.py",
    "lesson06_batch/main.py"
]


def main():
    for relative in LESSONS:
        print(f"==> {relative}")
        subprocess.run([sys.executable, str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

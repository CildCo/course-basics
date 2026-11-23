"""运行全部课次，任何一课失败立即退出。"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_baseline/main.py",
    "lesson02_forest/main.py",
    "lesson03_boosting/main.py",
    "lesson04_encoding/main.py",
    "lesson05_imbalance/main.py",
    "lesson06_calibration/main.py",
    "lesson07_explain/main.py",
    "lesson08_ensemble/main.py",
    "lesson09_search/main.py",
    "lesson10_project/main.py"
]
RUNNERS = {
    ".py": [sys.executable],
    ".sh": [shutil.which("bash") or "bash"],
    ".js": [shutil.which("node") or "node"],
}


def main():
    for relative in LESSONS:
        command = RUNNERS.get(Path(relative).suffix)
        if not command:
            raise SystemExit(f"未知的课次类型：{relative}")
        print(f"==> {relative}")
        subprocess.run(command + [str(ROOT / relative)], check=True)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

"""运行全部课次，任何一课失败立即退出。"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_quality_dimensions/main.py",
    "lesson02_first_rule/main.py",
    "lesson03_rule_table/main.py",
    "lesson04_missing_duplicate/main.py",
    "lesson05_foreign_key/main.py",
    "lesson06_outlier_drift/main.py",
    "lesson07_report/main.py",
    "lesson08_quality_gate/main.py"
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

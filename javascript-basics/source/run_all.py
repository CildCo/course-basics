"""运行全部课次，任何一课失败立即退出。"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_first/main.js",
    "lesson02_types/main.js",
    "lesson03_functions/main.js",
    "lesson04_arrays_objects/main.js",
    "lesson05_json_modules/main.js",
    "lesson06_async/main.js",
    "lesson07_files/main.js",
    "lesson08_http/main.js",
    "lesson09_errors/main.js",
    "lesson10_miniprogram/main.js"
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

"""运行全部课次，任何一课失败立即退出。"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_framework/main.py",
    "lesson02_two_pointers/main.py",
    "lesson03_hash_counting/main.py",
    "lesson04_stack_queue/main.py",
    "lesson05_binary_search/main.py",
    "lesson06_tree_recursion/main.py",
    "lesson07_graph_search/main.py",
    "lesson08_dp_practice/main.py"
]
RUNNERS = {
    ".py": [sys.executable],
    ".sh": [shutil.which("bash") or "bash"],
    ".js": [shutil.which("node") or "node"],
}


def main():
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    for relative in LESSONS:
        command = RUNNERS.get(Path(relative).suffix)
        if not command:
            raise SystemExit(f"未知的课次类型：{relative}")
        print(f"==> {relative}", flush=True)
        subprocess.run(command + [str(ROOT / relative)], check=True, env=env)
    print("全部课次运行通过")


if __name__ == "__main__":
    main()

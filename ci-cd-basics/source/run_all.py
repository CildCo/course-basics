"""运行全部课次，任何一课失败立即退出。"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_concept/main.py",
    "lesson02_local_pipeline/main.py",
    "lesson03_artifacts_version/main.py",
    "lesson04_actions_yaml/main.py",
    "lesson05_secrets_rollback/main.py",
    "lesson06_project/main.py"
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

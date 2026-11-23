"""运行全部课次，任何一课失败立即退出。"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = [
    "lesson01_tensor/main.py",
    "lesson02_autograd/main.py",
    "lesson03_linear_from_scratch/main.py",
    "lesson04_module_optimizer/main.py",
    "lesson05_training_loop/main.py",
    "lesson06_logistic/main.py",
    "lesson07_regularization/main.py",
    "lesson08_cnn/main.py",
    "lesson09_save_load/main.py",
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

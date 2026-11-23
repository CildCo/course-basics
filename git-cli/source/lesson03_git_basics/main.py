import os
import shutil
import stat

def force_rmtree(path):
    def onerror(func, target, exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    shutil.rmtree(path, onerror=onerror)

import subprocess
from pathlib import Path

repo = Path("output") / "git-demo"
if repo.exists():
    force_rmtree(repo)
repo.mkdir(parents=True)

def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)

git("init")
git("config", "user.name", "小居")
git("config", "user.email", "learner@example.com")
print("仓库已初始化")


(repo / "hello.py").write_text("print('hello')\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "first commit")
print(git("log", "--format=%s").stdout.strip())


(repo / "hello.py").write_text("print('hello git')\n", encoding="utf-8")
print("状态：")
print(git("status", "--short").stdout.strip() or "工作区干净")
git("add", ".")
git("commit", "-m", "update greeting")
print("提交历史：")
print(git("log", "--format=%s").stdout.strip())

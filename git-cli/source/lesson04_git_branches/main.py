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

repo = Path("output") / "git-branches"
if repo.exists():
    force_rmtree(repo)
repo.mkdir(parents=True)

def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)

git("init")
git("config", "user.name", "小李")
git("config", "user.email", "learner@example.com")
(repo / "notes.txt").write_text("main line\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "initial")
main_branch = git("branch", "--show-current").stdout.strip()
print("主分支：", main_branch)


git("checkout", "-b", "feature")
(repo / "notes.txt").write_text("main line\nfeature line\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "add feature")
git("checkout", main_branch)
git("merge", "feature")
print(git("log", "--format=%s").stdout.strip())


git("checkout", "-b", "left")
(repo / "notes.txt").write_text("left version\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "left change")

git("checkout", main_branch)
git("checkout", "-b", "right")
(repo / "notes.txt").write_text("right version\n", encoding="utf-8")
git("add", ".")
git("commit", "-m", "right change")

git("checkout", "left")
merged = git("merge", "right", check=False)
print("合并返回码：", merged.returncode)
print((repo / "notes.txt").read_text(encoding="utf-8"))


(repo / "notes.txt").write_text("resolved version\n", encoding="utf-8")
git("add", "notes.txt")
git("commit", "-m", "resolve conflict")
print(git("log", "--format=%s").stdout.strip())
print(git("status", "--short").stdout.strip() or "工作区干净")

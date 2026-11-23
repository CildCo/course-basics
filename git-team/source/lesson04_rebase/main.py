import atexit
import os
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORK = Path(tempfile.mkdtemp(prefix="git-team-"))

def force_rmtree(path):
    def handle(func, target, exc_info):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    if path.exists():
        shutil.rmtree(path, onerror=handle)

atexit.register(force_rmtree, WORK)
CLOCK = [datetime(2026, 1, 1, 9, 0, tzinfo=timezone(timedelta(hours=8)))]

def next_date():
    CLOCK[0] += timedelta(minutes=5)
    return CLOCK[0].isoformat()

def git(repo, *args, check=True, env=None):
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if env:
        environment.update(env)
    result = subprocess.run(
        ["git", "-c", "color.ui=false", "-c", "core.quotepath=false", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result

def new_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "学员")
    git(path, "config", "user.email", "learner@example.com")
    git(path, "config", "core.autocrlf", "false")
    return path

def commit(repo, message):
    stamp = next_date()
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message, env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})

def tidy(text):
    return text.replace(str(WORK), "<demo>")

print("临时工作目录已创建，Notebook 结束时会自动删除。")


base = new_repo(WORK / "base")
(base / "app.py").write_text("VERSION = '1.0.0'\n", encoding="utf-8")
commit(base, "初始提交")

git(base, "checkout", "-b", "feature/search")
(base / "search.py").write_text(
    "def search(items, word):\n    return [item for item in items if word in item]\n",
    encoding="utf-8",
)
commit(base, "添加搜索")
(base / "search.py").write_text(
    "def search(items, word):\n    word = word.lower()\n"
    "    return [item for item in items if word in item.lower()]\n",
    encoding="utf-8",
)
commit(base, "忽略大小写")

git(base, "checkout", "main")
(base / "debug.py").write_text("DEBUG = False\n", encoding="utf-8")
commit(base, "添加调试开关")

print("分叉后的提交图：")
print(git(base, "log", "--graph", "--oneline", "--all", "--decorate").stdout.strip())


merge_repo = WORK / "merge-demo"
git(WORK, "clone", str(base), str(merge_repo))
git(merge_repo, "config", "user.name", "学员")
git(merge_repo, "config", "user.email", "learner@example.com")

git(merge_repo, "checkout", "main")
stamp = next_date()
git(
    merge_repo,
    "merge",
    "--no-ff",
    "origin/feature/search",
    "-m",
    "合并搜索功能",
    env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
)

print("merge 后的提交图：")
print(git(merge_repo, "log", "--graph", "--oneline", "--all", "--decorate").stdout.strip())


rebase_repo = WORK / "rebase-demo"
git(WORK, "clone", str(base), str(rebase_repo))
git(rebase_repo, "config", "user.name", "学员")
git(rebase_repo, "config", "user.email", "learner@example.com")

git(rebase_repo, "checkout", "-b", "feature/search", "origin/feature/search")
stamp = next_date()
git(rebase_repo, "rebase", "main", env={"GIT_COMMITTER_DATE": stamp})
git(rebase_repo, "checkout", "main")
git(rebase_repo, "merge", "--ff-only", "feature/search")

print("rebase 后的提交图：")
print(git(rebase_repo, "log", "--graph", "--oneline", "--all", "--decorate").stdout.strip())
print()
print("main 的直线历史：")
print(git(rebase_repo, "log", "--oneline", "main", "-5").stdout.strip())

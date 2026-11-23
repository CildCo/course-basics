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


REMOTE = WORK / "remote.git"
REMOTE.mkdir()
git(REMOTE, "init", "--bare", "-b", "main")

seed = new_repo(WORK / "seed")
(seed / "README.md").write_text("# 搜索服务\n", encoding="utf-8")
commit(seed, "初始提交")
git(seed, "remote", "add", "origin", str(REMOTE))
git(seed, "push", "-u", "origin", "main")

dev = WORK / "dev"
git(WORK, "clone", str(REMOTE), str(dev))
git(dev, "config", "user.name", "Dev")
git(dev, "config", "user.email", "dev@example.com")

git(dev, "checkout", "-b", "feature/search")
(dev / "search.py").write_text(
    "def search(items, word):\n    return [item for item in items if word in item]\n",
    encoding="utf-8",
)
commit(dev, "添加搜索函数")
(dev / "search.py").write_text(
    "def search(items, word):\n    word = word.lower()\n"
    "    return [item for item in items if word in item.lower()]\n",
    encoding="utf-8",
)
commit(dev, "搜索忽略大小写")
git(dev, "push", "-u", "origin", "feature/search")

print("推送后状态：", git(dev, "status", "-sb").stdout.strip())


reviewer = WORK / "reviewer"
git(WORK, "clone", str(REMOTE), str(reviewer))
git(reviewer, "config", "user.name", "Reviewer")
git(reviewer, "config", "user.email", "reviewer@example.com")
git(reviewer, "fetch")

print("待评审提交：")
print(git(reviewer, "log", "--oneline", "main..origin/feature/search").stdout.strip())
print()
print("改动统计：")
print(git(reviewer, "diff", "--stat", "main...origin/feature/search").stdout.strip())
print()
print("评审前 main 上有 search.py：", (reviewer / "search.py").exists())


request = git(dev, "request-pull", "main", "origin", "feature/search")
print(tidy(request.stdout).replace("\\", "/").strip())


stamp = next_date()
git(
    reviewer,
    "merge",
    "--no-ff",
    "origin/feature/search",
    "-m",
    "合并 PR：搜索功能",
    env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
)
git(reviewer, "push")

git(dev, "checkout", "main")
git(dev, "pull", "--ff-only")

print("合并后 main 的最近提交：")
print(git(dev, "log", "--oneline", "-3").stdout.strip())
print()
print("开发者状态：", git(dev, "status", "-sb").stdout.strip())

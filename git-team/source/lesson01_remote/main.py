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
(seed / "README.md").write_text("# 演示项目\n\n第一版。\n", encoding="utf-8")
commit(seed, "初始提交")
git(seed, "remote", "add", "origin", str(REMOTE))
git(seed, "push", "-u", "origin", "main")

print("远程仓库类型：bare")
print("seed 仓库状态：", git(seed, "status", "-sb").stdout.strip())
print("远程 main 最新提交：", git(seed, "log", "-1", "--format=%s", "origin/main").stdout.strip())


alice = WORK / "alice"
git(WORK, "clone", str(REMOTE), str(alice))
git(alice, "config", "user.name", "Alice")
git(alice, "config", "user.email", "alice@example.com")

(alice / "README.md").write_text(
    "# 演示项目\n\n第一版。\n\n用法：python app.py\n", encoding="utf-8"
)
commit(alice, "补充用法说明")
git(alice, "push")

print("clone 后 branch -vv：")
print(git(alice, "branch", "-vv").stdout.strip())
print("push 后状态：", git(alice, "status", "-sb").stdout.strip())


bob = WORK / "bob"
git(WORK, "clone", str(REMOTE), str(bob))
git(bob, "config", "user.name", "Bob")
git(bob, "config", "user.email", "bob@example.com")

(alice / "app.py").write_text("print('hello from app')\n", encoding="utf-8")
commit(alice, "添加入口脚本")
git(alice, "push")

before = git(bob, "log", "-1", "--format=%s").stdout.strip()
git(bob, "fetch")
remote_subject = git(bob, "log", "-1", "--format=%s", "origin/main").stdout.strip()
has_file_before_pull = (bob / "app.py").exists()
git(bob, "pull", "--ff-only")
has_file_after_pull = (bob / "app.py").exists()

print("fetch 前 Bob 的 HEAD：", before)
print("fetch 后远端 main：", remote_subject)
print("pull 前 Bob 有 app.py：", has_file_before_pull)
print("pull 后 Bob 有 app.py：", has_file_after_pull)
print("pull 后状态：", git(bob, "status", "-sb").stdout.strip())

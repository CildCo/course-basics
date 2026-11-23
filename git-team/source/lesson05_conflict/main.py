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


app = new_repo(WORK / "app")
(app / "config.txt").write_text("host=localhost\nport=8000\n", encoding="utf-8")
commit(app, "初始配置")

git(app, "checkout", "-b", "feature/timeout")
(app / "config.txt").write_text("host=localhost\nport=8080\n", encoding="utf-8")
commit(app, "修改端口")

git(app, "checkout", "main")
(app / "config.txt").write_text("host=127.0.0.1\nport=8000\n", encoding="utf-8")
commit(app, "修改主机")

result = git(app, "merge", "feature/timeout", check=False)
print("合并退出码：", result.returncode)
print("冲突状态：", git(app, "status", "--short").stdout.strip())
print()
print("冲突文件内容：")
print((app / "config.txt").read_text(encoding="utf-8").strip())


(app / "config.txt").write_text("host=127.0.0.1\nport=8080\n", encoding="utf-8")
git(app, "add", "config.txt")
stamp = next_date()
git(
    app,
    "commit",
    "--no-edit",
    env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
)

print("解决后的配置：")
print((app / "config.txt").read_text(encoding="utf-8").strip())
print()
print("最近提交：")
print(git(app, "log", "--format=%s", "-4").stdout.strip())


(app / "config.txt").write_text("host=127.0.0.1\nport=9999\n", encoding="utf-8")
commit(app, "错误的端口修改")
print("回滚前：", (app / "config.txt").read_text(encoding="utf-8").splitlines()[1])

stamp = next_date()
git(
    app,
    "revert",
    "--no-edit",
    "HEAD",
    env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
)
print("revert 后：", (app / "config.txt").read_text(encoding="utf-8").splitlines()[1])
print()
print("reflog 最近记录：")
print(git(app, "reflog", "--format=%gs", "-5").stdout.strip())


git(app, "reset", "--hard", "HEAD~1")
print("reset 后：", (app / "config.txt").read_text(encoding="utf-8").splitlines()[1])

git(app, "reset", "--hard", "HEAD@{1}")
print("用 reflog 恢复后：", (app / "config.txt").read_text(encoding="utf-8").splitlines()[1])
print("当前状态：", git(app, "status", "-sb").stdout.strip())

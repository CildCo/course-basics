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
(app / "app.py").write_text(
    "VERSION = '1.0.0'\n\ndef run():\n    return 'app'\n", encoding="utf-8"
)
commit(app, "初始化应用")

git(app, "checkout", "-b", "feature/login")
(app / "login.py").write_text(
    "def login(user):\n    return f'欢迎 {user}'\n", encoding="utf-8"
)
commit(app, "添加登录函数")
(app / "login.py").write_text(
    "def login(user, password):\n    if not password:\n        return '密码不能为空'\n"
    "    return f'欢迎 {user}'\n",
    encoding="utf-8",
)
commit(app, "登录增加密码校验")

git(app, "checkout", "main")
stamp = next_date()
git(
    app,
    "merge",
    "--no-ff",
    "feature/login",
    "-m",
    "合并登录功能",
    env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
)

print("合并登录功能后的提交图：")
print(git(app, "log", "--graph", "--oneline", "--all", "--decorate").stdout.strip())


git(app, "checkout", "-b", "release/1.0")
(app / "app.py").write_text(
    "VERSION = '1.0.0'\n\nRELEASE_NOTES = '首个版本'\n\n"
    "def run():\n    return 'app'\n",
    encoding="utf-8",
)
commit(app, "准备 1.0 发布")

git(app, "checkout", "main")
stamp = next_date()
git(
    app,
    "merge",
    "--no-ff",
    "release/1.0",
    "-m",
    "合并 release/1.0",
    env={"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
)

print("分支列表：")
print(git(app, "branch", "-vv").stdout.strip())
print()
print("最终提交图：")
print(git(app, "log", "--graph", "--oneline", "--all", "--decorate").stdout.strip())

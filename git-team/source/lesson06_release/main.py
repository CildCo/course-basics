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
    "VERSION = '1.0.0'\n\ndef run():\n    return VERSION\n", encoding="utf-8"
)
(app / "requirements.txt").write_text("# 示例项目只用标准库\n", encoding="utf-8")
commit(app, "准备 1.0.0")

git(app, "tag", "-a", "v1.0.0", "-m", "发布 1.0.0")
print("标签列表：")
print(git(app, "tag", "-n").stdout.strip())
print()
print("当前版本描述：", git(app, "describe", "--tags").stdout.strip())


release_zip = WORK / "app-1.0.0.zip"
git(
    app,
    "archive",
    "--format=zip",
    "--prefix=app-1.0.0/",
    "-o",
    str(release_zip),
    "v1.0.0",
)

import zipfile

with zipfile.ZipFile(release_zip) as archive:
    names = sorted(archive.namelist())
print("发布包内容：")
for name in names:
    print(" ", name)
print("文件数：", len(names))


workflow = """name: release

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -r requirements.txt
      - run: git archive --format=zip --prefix=release/ -o release.zip HEAD
      - uses: actions/upload-artifact@v4
        with:
          name: release
          path: release.zip
"""

workflow_dir = app / ".github" / "workflows"
workflow_dir.mkdir(parents=True)
(workflow_dir / "release.yml").write_text(workflow, encoding="utf-8")
commit(app, "添加发布工作流")

print("工作流文件：.github/workflows/release.yml")
print("包含触发标签规则：", 'tags:' in workflow)
print("包含打包步骤：", "git archive" in workflow)


(app / "app.py").write_text(
    "VERSION = '1.1.0'\n\ndef run():\n    return VERSION\n", encoding="utf-8"
)
commit(app, "升级到 1.1.0")
git(app, "tag", "-a", "v1.1.0", "-m", "发布 1.1.0")

print("全部标签：")
print(git(app, "tag", "-n").stdout.strip())
print()
print("当前版本描述：", git(app, "describe", "--tags").stdout.strip())
print()
print("最近提交：")
print(git(app, "log", "--oneline", "-4").stdout.strip())

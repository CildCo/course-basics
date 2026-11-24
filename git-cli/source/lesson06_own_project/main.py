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

project = Path("output") / "my-project"
if project.exists():
    force_rmtree(project)
project.mkdir(parents=True)

(project / "main.py").write_text(
    "def main():\n    print('我的第一个项目')\n\nif __name__ == '__main__':\n    main()\n",
    encoding="utf-8",
)
(project / "README.md").write_text("# 我的第一个项目\n\n运行：python main.py\n", encoding="utf-8")
(project / ".gitignore").write_text(".venv/\n__pycache__/\noutput/\n", encoding="utf-8")
print(sorted(path.name for path in project.iterdir()))


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)

git("init")
git("config", "user.name", "小李")
git("config", "user.email", "learner@example.com")
git("add", ".")
git("commit", "-m", "initial project")
print(git("log", "--format=%s").stdout.strip())
print(git("status", "--short").stdout.strip() or "工作区干净")


import sys
result = subprocess.run([sys.executable, "main.py"], cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
print(result.stdout.strip())

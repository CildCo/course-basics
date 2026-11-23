import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT = Path.cwd() / "output" / "taskkit_project"
PACKAGE = PROJECT / "taskkit"
if PROJECT.exists():
    shutil.rmtree(PROJECT)
PACKAGE.mkdir(parents=True)


def write(relative, text):
    path = PROJECT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


write("taskkit/__init__.py", '__version__ = "0.1.0"\n')
write(
    "taskkit/cli.py",
    '''
    import click

    from . import __version__

    TASKS = ["整理课程大纲", "补充示例数据", "录制命令行演示"]


    @click.command()
    @click.option("-n", "--count", default=2, show_default=True, help="显示的任务数量")
    @click.version_option(__version__, prog_name="taskkit")
    def main(count):
        """打印待办任务。"""
        for index, title in enumerate(TASKS[:count], 1):
            click.echo(f"{index}. {title}")
    ''',
)
write(
    "taskkit/__main__.py",
    '''
    from .cli import main

    main()
    ''',
)
write(
    "pyproject.toml",
    '''
    [build-system]
    requires = ["setuptools>=68"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "taskkit"
    version = "0.1.0"
    requires-python = ">=3.9"
    dependencies = ["click>=8.0"]

    [project.scripts]
    taskkit = "taskkit.cli:main"

    [tool.setuptools.packages.find]
    where = ["."]
    ''',
)

if __name__ == "__main__":
    print((PROJECT / "pyproject.toml").read_text(encoding="utf-8"))


def run_module(*args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-m", "taskkit", *args],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print("$ python -m taskkit", " ".join(args))
    print(result.stdout.strip())
    if result.stderr.strip():
        print("[stderr]", result.stderr.strip())
    print("退出码：", result.returncode)
    print()


if __name__ == "__main__":
    run_module("-n", "2")
    run_module("--version")


import tomllib

if __name__ == "__main__":
    data = tomllib.loads((PROJECT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    print("命令名：", list(scripts))
    print("入口：", scripts["taskkit"])
    import_path, function_name = scripts["taskkit"].split(":")
    print("模块：", import_path, "函数：", function_name)
    print("依赖：", data["project"]["dependencies"])


if __name__ == "__main__":
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT)
    env["PYTHONIOENCODING"] = "utf-8"
    help_result = subprocess.run(
        [sys.executable, "-m", "taskkit", "--help"],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(help_result.stdout.strip())


if __name__ == "__main__":
    shutil.rmtree(PROJECT, ignore_errors=True)
    print("临时包目录已清理：", not PROJECT.exists())

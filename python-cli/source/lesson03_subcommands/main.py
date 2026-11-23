import json
from pathlib import Path

import click


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


TASKS = json.loads(data_path("tasks.json").read_text(encoding="utf-8"))


@click.group("taskkit")
def cli():
    """管理待办任务。"""


if __name__ == "__main__":
    print("读取任务数：", len(TASKS))
    print("命令对象类型：", type(cli).__name__)


@cli.command("list")
@click.option(
    "--status",
    type=click.Choice(["all", "open", "done"]),
    default="all",
    show_default=True,
)
def list_tasks(status):
    """列出任务。"""
    rows = TASKS
    if status == "open":
        rows = [task for task in TASKS if not task["done"]]
    elif status == "done":
        rows = [task for task in TASKS if task["done"]]
    for task in rows:
        mark = "x" if task["done"] else " "
        click.echo(f"[{mark}] {task['id']} {task['title']} ({task['priority']})")


@cli.command()
@click.argument("title")
@click.option(
    "--priority",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    show_default=True,
)
def add(title, priority):
    """新增一条任务。"""
    next_id = max(task["id"] for task in TASKS) + 1 if TASKS else 1
    TASKS.append(
        {"id": next_id, "title": title, "priority": priority, "done": False}
    )
    click.echo(f"已添加 #{next_id} {title}")


@cli.command()
@click.argument("task_id", type=int)
def done(task_id):
    """把任务标记为完成。"""
    task = next((item for item in TASKS if item["id"] == task_id), None)
    if task is None:
        raise click.ClickException(f"没有编号为 {task_id} 的任务")
    if task["done"]:
        click.echo(f"#{task_id} 已经是完成状态")
        return
    task["done"] = True
    click.echo(f"已完成 #{task_id} {task['title']}")


if __name__ == "__main__":
    print("已注册子命令：", sorted(cli.commands))


from click.testing import CliRunner


def run(*args):
    result = CliRunner().invoke(cli, list(args))
    print(f"$ taskkit {' '.join(args)}")
    print(result.output.strip())
    print("退出码：", result.exit_code)
    print()


if __name__ == "__main__":
    run("list", "--status", "open")
    run("add", "写发布说明", "--priority", "high")
    run("done", "2")
    run("list", "--status", "done")


if __name__ == "__main__":
    run("done", "99")
    run("add", "错误的优先级", "--priority", "urgent")

import click


@click.command()
@click.argument("path")
@click.option("-n", "--count", default=3, show_default=True, help="最多显示的行数")
@click.option("--upper", is_flag=True, help="把结果转成大写")
def preview(path, count, upper):
    """预览文件的前几行。"""
    lines = [f"{path} 的第 {index} 行" for index in range(1, count + 1)]
    if upper:
        lines = [line.upper() for line in lines]
    for line in lines:
        click.echo(line)


if __name__ == "__main__":
    print("装饰后的对象类型：", type(preview).__name__)


from click.testing import CliRunner


if __name__ == "__main__":
    runner = CliRunner()
    result = runner.invoke(preview, ["notes.txt", "-n", "2"])
    print("退出码：", result.exit_code)
    print(result.output, end="")


if __name__ == "__main__":
    runner = CliRunner()

    help_result = runner.invoke(preview, ["--help"])
    print(help_result.output)

    missing_result = runner.invoke(preview, [])
    print("缺少参数退出码：", missing_result.exit_code)
    print(missing_result.output.strip())


if __name__ == "__main__":
    runner = CliRunner()
    result = runner.invoke(preview, ["notes.txt", "--upper", "-n", "2"])
    print("退出码：", result.exit_code)
    print(result.output, end="")

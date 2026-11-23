import argparse


def build_parser():
    parser = argparse.ArgumentParser(prog="lines", description="统计文本文件的行数")
    parser.add_argument("path", help="要统计的文件路径")
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=3,
        help="最多显示的行数，默认 3",
    )
    parser.add_argument("--verbose", action="store_true", help="输出详细信息")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args(["notes.txt", "--count", "5", "--verbose"])
    print(args)
    print("count 的类型：", type(args.count).__name__)
    print("转成字典：", vars(args))


if __name__ == "__main__":
    parser = build_parser()
    default_args = parser.parse_args(["notes.txt"])
    print("使用默认值：", default_args.count, default_args.verbose)

    short_args = parser.parse_args(["notes.txt", "-n", "0"])
    print("短选项写法：", short_args.count, type(short_args.count).__name__)


import contextlib
import io


if __name__ == "__main__":
    parser = build_parser()

    help_output = io.StringIO()
    with contextlib.redirect_stdout(help_output):
        try:
            parser.parse_args(["--help"])
        except SystemExit as exc:
            help_exit = exc.code
    print("帮助退出码：", help_exit)
    print(help_output.getvalue().strip())

    error_output = io.StringIO()
    with contextlib.redirect_stderr(error_output):
        try:
            parser.parse_args(["notes.txt", "--count", "many"])
        except SystemExit as exc:
            error_exit = exc.code
    print()
    print("非法参数退出码：", error_exit)
    print(error_output.getvalue().strip())


if __name__ == "__main__":
    parser = build_parser()
    known, unknown = parser.parse_known_args(["notes.txt", "--color", "always"])
    print("已知参数：", known)
    print("留给其他工具：", unknown)

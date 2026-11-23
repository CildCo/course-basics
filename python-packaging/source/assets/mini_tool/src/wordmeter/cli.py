"""命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import count_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wordmeter",
        description="统计文本文件的行数、词数和字符数",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="文本文件路径；省略或写 - 时从标准输入读取",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.path in (None, "-"):
        text = sys.stdin.read()
    else:
        text = Path(args.path).read_text(encoding="utf-8")
    stats = count_text(text)
    if args.json:
        print(json.dumps(stats.__dict__, ensure_ascii=False, indent=2))
    else:
        print(f"行数：{stats.lines}")
        print(f"词数：{stats.words}")
        print(f"字符：{stats.chars}")
        print(f"中文：{stats.cjk}")
    return 0

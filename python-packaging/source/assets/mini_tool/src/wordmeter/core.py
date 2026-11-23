"""文本统计的核心逻辑，不依赖命令行参数。"""

from __future__ import annotations

import re
from dataclasses import dataclass

_WORD = re.compile(r"[A-Za-z0-9_]+")
_CJK = re.compile(r"[一-鿿]")


@dataclass(frozen=True)
class TextStats:
    """一次统计的结果。"""

    lines: int
    words: int
    chars: int
    cjk: int


def count_text(text: str) -> TextStats:
    """统计行数、词数、字符数和中文字符数。"""
    if text:
        lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    else:
        lines = 0
    cjk = len(_CJK.findall(text))
    words = len(_WORD.findall(text)) + cjk
    return TextStats(lines=lines, words=words, chars=len(text), cjk=cjk)

"""统计文本行数、词数与字符数的小工具。"""

__version__ = "0.1.0"

from .core import TextStats, count_text

__all__ = ["TextStats", "count_text", "__version__"]

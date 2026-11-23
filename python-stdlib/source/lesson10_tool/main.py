import argparse

def build_parser():
    parser = argparse.ArgumentParser(
        prog="wordcount",
        description="统计文本里的高频词",
    )
    parser.add_argument("path", help="要统计的文本文件")
    parser.add_argument("--top", type=int, default=3, help="显示前几个词")
    return parser

parser = build_parser()
demo_args = parser.parse_args(["notes.txt", "--top", "2"])
print("文件：", demo_args.path)
print("数量：", demo_args.top)


from collections import Counter
from pathlib import Path

def count_words(path: Path, top: int):
    text = path.read_text(encoding="utf-8").lower()
    words = [word.strip(".,!?") for word in text.split()]
    words = [word for word in words if word]
    return Counter(words).most_common(top)

sample = Path("sample.txt")
print("统计函数已准备好：", count_words.__name__)


import logging
import tempfile
from io import StringIO

tmp = tempfile.TemporaryDirectory()
root = Path(tmp.name)
sample = root / "sample.txt"
sample.write_text("Python stdlib python tools python data tools", encoding="utf-8")

stream = StringIO()
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    stream=stream,
    force=True,
)
logger = logging.getLogger("wordcount")

args = parser.parse_args([str(sample), "--top", "2"])
logger.info("读取文件 %s", sample.name)
logger.info("统计前 %d 个词", args.top)
print(stream.getvalue().strip())

for word, count in count_words(Path(args.path), args.top):
    print(f"{word}: {count}")

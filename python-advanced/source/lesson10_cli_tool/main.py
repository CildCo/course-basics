from pathlib import Path
import csv
import logging

def read_scores(path):
    with Path(path).open(encoding="utf-8", newline="") as file:
        return [{"name": row["name"], "score": int(row["score"])} for row in csv.DictReader(file)]

def summarize(rows):
    scores = [row["score"] for row in rows]
    return {"count": len(scores), "average": round(sum(scores) / len(scores), 1), "max": max(scores)}

print(summarize([{"name": "小居", "score": 88}, {"name": "小明", "score": 95}]))


import argparse

def build_parser():
    parser = argparse.ArgumentParser(description="统计成绩 CSV")
    parser.add_argument("path", help="CSV 文件路径")
    parser.add_argument("--min", type=int, default=0, help="只统计不低于这个分数的记录")
    return parser

parser = build_parser()
print(parser.parse_args(["scores.csv", "--min", "60"]))


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    rows = [row for row in read_scores(args.path) if row["score"] >= args.min]
    if not rows:
        logging.error("没有符合条件的记录")
        return 1
    result = summarize(rows)
    logging.info("统计完成：%s", result)
    return 0

output = Path("output")
output.mkdir(exist_ok=True)
path = output / "scores.csv"
path.write_text("name,score\n小居,88\n小明,95\n小红,59\n", encoding="utf-8")
print("退出码：", main([str(path), "--min", "60"]))

#!/usr/bin/env bash
set -euo pipefail

set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "数据目录：$DATA"
ls -lh "$DATA"


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/demo/logs" "$TMP/demo/data"
cp "$DATA/sample.log" "$TMP/demo/logs/app.log"
cp "$DATA/sales.csv" "$TMP/demo/data/"
echo "== 目录里的文件 =="
find "$TMP/demo" -type f | sort
echo "== 复制后的日志大小 =="
ls -lh "$TMP/demo/logs/app.log"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/work"
touch "$TMP/work/draft.txt" "$TMP/work/note.txt"
mv "$TMP/work/draft.txt" "$TMP/work/final.txt"
echo "== 改名后 =="
ls -1 "$TMP/work"
rm "$TMP/work/note.txt"
echo "== 删除一个文件后 =="
ls -1 "$TMP/work"
mkdir -p "$TMP/work/old"
touch "$TMP/work/old/a.log"
rm -r "$TMP/work/old"
echo "== 删除子目录后 =="
find "$TMP/work" -mindepth 1
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
touch report-2026-09.csv report-2026-10.csv notes.txt app.log
echo "== 所有 csv =="
ls *.csv
echo "== 只匹配 10 月（? 代表一个字符）=="
ls report-2026-1?.csv
echo "== 删除所有报表 =="
rm report-2026-*.csv
ls -1
cd - >/dev/null
rm -rf "$TMP"


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "== 按后缀查找文件 =="
find "$DATA" -maxdepth 1 -type f -name "*.log" -printf "%f %s 字节\n"
echo "== 按大小排序 =="
du -h "$DATA"/* | sort -h
echo "== 目录总大小 =="
du -sh "$DATA"

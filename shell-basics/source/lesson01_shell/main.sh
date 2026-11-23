#!/usr/bin/env bash
set -euo pipefail

set -e
echo "当前 Shell：$BASH_VERSION"
echo "当前用户：$(whoami)"
echo "主目录：$HOME"
echo "当前目录：$(pwd)"


set -e
echo "== 内置命令 =="
type cd
echo "== 外部程序 =="
type sed
command -v awk


set -e
START=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/project/logs"
cd "$TMP/project"
echo "项目目录（绝对路径）：$(pwd)"
cd logs
echo "进入子目录：$(pwd)"
cd ..
echo "回到上一层：$(pwd)"
echo "绝对路径示例：$TMP/project/logs"
cd "$START"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
if ls "$TMP/not-here" >/dev/null 2>&1; then
  echo "命令成功，退出码 0"
else
  echo "命令失败，退出码 $?"
fi
if cp "$TMP/missing.txt" "$TMP/copy.txt" 2>/dev/null; then
  echo "复制成功"
else
  echo "复制失败，退出码 $?"
fi
rm -rf "$TMP"


set -e
echo "== ls 的常用选项 =="
ls --help | head -4
echo "== sed 的用法摘要 =="
sed --help | head -3

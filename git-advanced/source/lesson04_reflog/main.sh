#!/usr/bin/env bash
set -euo pipefail

set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
printf "def search(items):\n    return items\n" > search.py
git add search.py
git commit -q -m "添加搜索"
printf "def search(items):\n    return [x for x in items if x]\n" > search.py
git add search.py
git commit -q -m "过滤空值"
printf "def search(items):\n    return sorted(x for x in items if x)\n" > search.py
git add search.py
git commit -q -m "结果排序"
echo "== reset 前的历史 =="
git log --oneline
git reset --hard HEAD~2
echo "== reset 后的历史 =="
git log --oneline
echo "== reflog =="
git reflog --format='%h %gs' -5
git reset --hard HEAD@{1}
echo "== 恢复后的历史 =="
git log --oneline
cat search.py
cd "$ORIGIN"
rm -rf "$TMP"


set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
printf "print('app')\n" > app.py
git add app.py
git commit -q -m "初始化项目"
git checkout -q -b feature/export
printf "def export_csv(rows):\n    return [','.join(map(str, row)) for row in rows]\n" > export_csv.py
git add export_csv.py
git commit -q -m "添加 CSV 导出"
printf "def export_csv(rows):\n    lines = [','.join(map(str, row)) for row in rows]\n    return '\\n'.join(lines)\n" > export_csv.py
git add export_csv.py
git commit -q -m "补上换行连接"
git checkout -q main
git branch -D feature/export
echo "== 当前分支 =="
git branch
echo "== reflog 里的线索 =="
git reflog --format='%h %gs' -8
HASH=$(git reflog --format='%H %gs' | grep "补上换行连接" | head -1 | cut -d' ' -f1)
git branch rescue "$HASH"
echo "== 恢复出来的分支 =="
git log --oneline rescue
cd "$ORIGIN"
rm -rf "$TMP"

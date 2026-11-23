#!/usr/bin/env bash
set -euo pipefail

set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir "$TMP/repo"
cd "$TMP/repo"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
printf "VERSION = '1.0.0'\n" > app.py
git add app.py
git commit -q -m "初始化项目"
git checkout -q -b feature/search
printf "def search():\n    return []\n" > search.py
git add search.py
git commit -q -m "feat: 搜索"
git checkout -q main
git worktree add "$TMP/feature-wt" feature/search
echo "== 工作区列表 =="
git worktree list
echo "== 功能分支工作区内容 =="
ls "$TMP/feature-wt"
git worktree remove "$TMP/feature-wt"
echo "== 移除后的工作区列表 =="
git worktree list
cd "$ORIGIN"
rm -rf "$TMP"


set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir "$TMP/repo"
cd "$TMP/repo"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
printf "VERSION = '1.0.0'\n" > app.py
git add app.py
git commit -q -m "初始化项目"
git branch feature/export
git worktree add "$TMP/export-wt" feature/export
printf "def export_csv(rows):\n    return ','.join(rows)\n" > "$TMP/export-wt/export.py"
git -C "$TMP/export-wt" add export.py
git -C "$TMP/export-wt" commit -q -m "feat: 导出 CSV"
printf "def health():\n    return 'ok'\n" > health.py
git add health.py
git commit -q -m "feat: 健康检查"
echo "== 主工作区看不到功能分支的新文件 =="
ls
echo "== 两个工作区各自的最新提交 =="
git log -1 --oneline main
git -C "$TMP/export-wt" log -1 --oneline feature/export
echo "== 合并功能分支 =="
git merge --no-ff feature/export -m "合并导出功能"
git log --oneline --graph --decorate --all
git worktree remove "$TMP/export-wt"
echo "== 清理后的工作区 =="
git worktree list
cd "$ORIGIN"
rm -rf "$TMP"

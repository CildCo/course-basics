#!/usr/bin/env bash
set -euo pipefail

set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
if [ -f assets/commit-msg ]; then ASSETS="$(pwd)/assets"; elif [ -f ../assets/commit-msg ]; then ASSETS="$(pwd)/../assets"; else echo "找不到 assets/commit-msg"; exit 1; fi
cd "$TMP"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
cp "$ASSETS/commit-msg" .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
printf "print('app')\n" > app.py
git add app.py
echo "== 第一次：普通描述 =="
if git commit -q -m "改了点东西"; then
  echo "提交成功"
else
  echo "提交被拒绝"
fi
echo "== 第二次：符合规范 =="
git commit -q -m "feat: 增加入口"
git log --oneline
cd "$ORIGIN"
rm -rf "$TMP"


set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
if [ -f assets/pre-commit ]; then ASSETS="$(pwd)/assets"; elif [ -f ../assets/pre-commit ]; then ASSETS="$(pwd)/../assets"; else echo "找不到 assets/pre-commit"; exit 1; fi
cd "$TMP"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
mkdir .githooks
cp "$ASSETS/pre-commit" .githooks/pre-commit
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
git add .githooks/pre-commit
git commit -q -m "chore: 添加提交前检查"
printf "def add(a, b):\n    return a + b   \n" > calc.py
git add calc.py
echo "== 第一次：带行尾空白 =="
if git commit -q -m "feat: 添加加法"; then
  echo "提交成功"
else
  echo "提交被拒绝"
fi
sed -i 's/[[:space:]]*$//' calc.py
git add calc.py
echo "== 第二次：清理空白后 =="
git commit -q -m "feat: 添加加法"
git log --oneline
cat calc.py
cd "$ORIGIN"
rm -rf "$TMP"

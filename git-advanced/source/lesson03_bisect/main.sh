#!/usr/bin/env bash
set -euo pipefail

set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
if [ -f assets/check.sh ]; then ASSETS="$(pwd)/assets"; elif [ -f ../assets/check.sh ]; then ASSETS="$(pwd)/../assets"; else echo "找不到 assets/check.sh"; exit 1; fi
cd "$TMP"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
cp "$ASSETS/check.sh" check.sh
chmod +x check.sh
printf "VERSION = '1.0.0'\n" > app.py
git add app.py check.sh
git commit -q -m "添加版本检查"
for i in $(seq 1 12); do
  printf "VERSION = '1.0.%s'\n" "$i" > app.py
  if [ "$i" -ge 7 ]; then
    printf "BROKEN = True\n" >> app.py
  fi
  git add app.py
  git commit -q -m "release 1.0.$i"
done
echo "== HEAD 的检查结果 =="
if bash check.sh; then
  echo "退出码 0，正常"
else
  echo "退出码 1，发现问题"
fi
echo "== 最近 5 个提交 =="
git log --oneline -5
cd "$ORIGIN"
rm -rf "$TMP"


set -e
ORIGIN=$(pwd)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
if [ -f assets/check.sh ]; then ASSETS="$(pwd)/assets"; elif [ -f ../assets/check.sh ]; then ASSETS="$(pwd)/../assets"; else echo "找不到 assets/check.sh"; exit 1; fi
cd "$TMP"
git init -q -b main
git config user.name "学员"
git config user.email "learner@example.com"
git config core.autocrlf false
cp "$ASSETS/check.sh" check.sh
chmod +x check.sh
printf "VERSION = '1.0.0'\n" > app.py
git add app.py check.sh
git commit -q -m "添加版本检查"
for i in $(seq 1 12); do
  printf "VERSION = '1.0.%s'\n" "$i" > app.py
  if [ "$i" -ge 7 ]; then
    printf "BROKEN = True\n" >> app.py
  fi
  git add app.py
  git commit -q -m "release 1.0.$i"
done
git bisect start HEAD HEAD~12
git bisect run bash check.sh
BAD=$(git rev-parse HEAD)
git bisect reset
echo "== 定位结果 =="
git log -1 --format="%h %s" "$BAD"
cd "$ORIGIN"
rm -rf "$TMP"

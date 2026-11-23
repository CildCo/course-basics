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
printf "ROWS = [('苹果', 3), ('香蕉', 5)]\n" > data.py
git add data.py
git commit -q -m "初始化数据"
git checkout -q -b feature/export
cat > export_csv.py <<'EOF'
def export_csv(rows):
    return "\n".join(f"{name},{count}" for name, count in rows)
EOF
git add export_csv.py
git commit -q -m "添加 CSV 导出"
cat > export_json.py <<'EOF'
import json

def export_json(rows):
    return json.dumps(rows, ensure_ascii=False)
EOF
git add export_json.py
git commit -q -m "添加 JSON 导出"
git checkout -q main
CSV_COMMIT=$(git rev-parse feature/export~1)
echo "只搬 CSV 这一个提交：$(git log -1 --oneline "$CSV_COMMIT")"
git cherry-pick "$CSV_COMMIT"
echo "== main 的历史 =="
git log --oneline --graph --all --decorate
echo "== main 根目录 =="
ls
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
printf "VERSION = '1.0.0'\n" > app.py
git add app.py
git commit -q -m "初始化项目"
git checkout -q -b feature/report
printf "def report():\n    return '日报'\n" > report.py
git add report.py
git commit -q -m "添加日报"
printf "def report_week():\n    return '周报'\n" > report_week.py
git add report_week.py
git commit -q -m "添加周报"
git checkout -q main
printf "DEBUG = False\n" > debug.py
git add debug.py
git commit -q -m "关闭调试"
git cherry-pick -x feature/report~2..feature/report
echo "== main 的历史 =="
git log --oneline --decorate
echo "== 最近一次提交的正文 =="
git log -1 --format="%h %s%n%b"
echo "== git cherry 检查补丁是否已在 main =="
git cherry -v main feature/report
cd "$ORIGIN"
rm -rf "$TMP"

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
printf "VERSION = '1.0.0'\n" > app.py
git add app.py
git commit -q -m "初始化项目"
git checkout -q -b feature/search
cat > search.py <<'EOF'
def search(items, word):
    return [item for item in items if word in item]
EOF
git add search.py
git commit -q -m "wip 搜索"
cat > search.py <<'EOF'
def search(items, word):
    word = word.lower()
    return [item for item in items if word in item.lower()]
EOF
git add search.py
git commit -q -m "wip 忽略大小写"
git checkout -q main
printf "DEBUG = False\n" > debug.py
git add debug.py
git commit -q -m "关闭调试开关"
echo "== 分叉的提交图 =="
git log --oneline --graph --all --decorate
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
git checkout -q -b feature/search
cat > search.py <<'EOF'
def search(items, word):
    return [item for item in items if word in item]
EOF
git add search.py
git commit -q -m "支持按名称搜索"
cat > search.py <<'EOF'
def search(items, word):
    word = word.lower()
    return [item for item in items if word in item.lower()]
EOF
git add search.py
git commit -q -m "忽略大小写"
git checkout -q main
printf "DEBUG = False\n" > debug.py
git add debug.py
git commit -q -m "关闭调试开关"
git checkout -q feature/search
git rebase -q main
echo "== rebase 之后 =="
git log --oneline --graph --all --decorate
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
printf "x = 1\n" > app.py
git add app.py
git commit -q -m "初始化"
printf "x = 2\n" > app.py
git add app.py
git commit -q -m "wip 第一步"
printf "x = 3\n" > app.py
git add app.py
git commit -q -m "wip 第二步"
printf "x = 4\n" > app.py
git add app.py
git commit -q -m "wip 第三步"
echo "== 整理前 =="
git log --oneline
cat > "$TMP/squash.sh" <<'EOF'
#!/usr/bin/env bash
sed -i '2,3s/^pick/squash/' "$1"
EOF
chmod +x "$TMP/squash.sh"
GIT_SEQUENCE_EDITOR="$TMP/squash.sh" GIT_EDITOR=true git rebase -q -i HEAD~3
git commit --amend -q -m "feat: 支持计数递增"
echo "== 整理后 =="
git log --oneline --graph
cd "$ORIGIN"
rm -rf "$TMP"

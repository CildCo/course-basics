#!/usr/bin/env bash
set -euo pipefail

set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "== 各级别日志条数 =="
awk '{print $3}' "$DATA/sample.log" | sort | uniq -c | sort -rn


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
grep 'ERROR' "$DATA/sample.log" > "$TMP/errors.log"
echo "第一次写入行数：$(wc -l < "$TMP/errors.log")"
grep 'payment-service' "$DATA/sample.log" | head -2 >> "$TMP/errors.log"
echo "追加后行数：$(wc -l < "$TMP/errors.log")"
echo "== 文件开头 =="
head -2 "$TMP/errors.log"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
ls "$TMP/not-here" > "$TMP/stdout.txt" 2> "$TMP/stderr.txt" || true
echo "标准输出字节数：$(wc -c < "$TMP/stdout.txt")"
echo "错误输出第一行：$(head -1 "$TMP/stderr.txt")"
ls "$TMP/not-here" 2>/dev/null || echo "错误已丢弃，退出码 $?"
rm -rf "$TMP"


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
echo "== 屏幕和文件同时得到内容 =="
awk '{print $6}' "$DATA/sample.log" | sort | uniq -c | sort -rn | tee "$TMP/status.txt" | head -5
echo "文件行数：$(wc -l < "$TMP/status.txt")"
rm -rf "$TMP"


set -e
COURSE="shell-basics"
echo "变量值：$COURSE"
export COURSE
MODE=child bash -c 'echo "子进程看到 COURSE=$COURSE，MODE=$MODE"'
unset MODE
echo "父进程的 MODE：${MODE:-未设置}"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
printf '#!/usr/bin/env bash\necho "自定义命令 hello 运行成功"\n' > "$TMP/hello"
chmod +x "$TMP/hello"
echo "== PATH 的前 3 项 =="
echo "$PATH" | tr ':' '\n' | head -3
PATH="$TMP:$PATH"
export PATH
hello
PATH="${PATH#"$TMP:"}"
rm -rf "$TMP"

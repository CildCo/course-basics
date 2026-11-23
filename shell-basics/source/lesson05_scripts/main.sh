#!/usr/bin/env bash
set -euo pipefail

set -e
NAME="码袋子"
COUNT=3
CODE="shell-basics"
echo "欢迎来到 $NAME，共 $COUNT 课"
echo '单引号原样输出：$NAME'
echo "双引号展开变量：$NAME"
echo "默认值：${UNSET_VALUE:-默认值}"
echo "变量长度：${#CODE}"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/greet.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
name="${1:-同学}"
shift || true
echo "你好，$name"
echo "其余参数：$*"
SCRIPT
bash "$TMP/greet.sh" 小明 九月 十月
bash "$TMP/greet.sh"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
cat > "$TMP/grade.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
score="${1:-0}"
if [ "$score" -ge 90 ]; then
  echo "$score 分：优秀"
elif [ "$score" -ge 60 ]; then
  echo "$score 分：及格"
else
  echo "$score 分：需要补课"
fi

case "${2:-status}" in
  start) echo "启动服务" ;;
  stop) echo "停止服务" ;;
  *) echo "未知操作：${2:-status}" ;;
esac
SCRIPT
bash "$TMP/grade.sh" 95 start
bash "$TMP/grade.sh" 72
bash "$TMP/grade.sh" 40 stop
rm -rf "$TMP"


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "== for 遍历文件 =="
for file in "$DATA"/*; do
  printf '%-12s %s 行\n' "$(basename "$file")" "$(wc -l < "$file")"
done
echo "== while 逐行统计 ERROR =="
count=0
while read -r date time level rest; do
  if [ "$level" = "ERROR" ]; then
    count=$((count + 1))
  fi
done < "$DATA/sample.log"
echo "ERROR 行数：$count"


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
export DATA
cat > "$TMP/report.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
count_level() {
  grep -c "$1" "$DATA/sample.log" || true
}
print_report() {
  echo "日志级别统计"
  for level in INFO WARN ERROR; do
    printf '%-6s %s\n' "$level" "$(count_level "$level")"
  done
}
print_report
SCRIPT
bash "$TMP/report.sh"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
cleanup() {
  echo "清理临时目录：$TMP"
  rm -rf "$TMP"
}
trap cleanup EXIT
echo "临时目录已创建"
ls -d "$TMP"

#!/usr/bin/env bash
set -euo pipefail

set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "ERROR 条数：$(grep -c 'ERROR' "$DATA/sample.log")"
echo "== 带行号的前 3 条 ERROR =="
grep -n 'ERROR' "$DATA/sample.log" | head -3
echo "== 支付服务的日志 =="
grep 'payment-service' "$DATA/sample.log" | head -3


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "== 非 INFO 记录 =="
grep -v 'INFO' "$DATA/sample.log" | head -4
echo "== ERROR 或 WARN 的总数 =="
grep -E 'ERROR|WARN' "$DATA/sample.log" | wc -l
echo "== 忽略大小写统计 error =="
grep -i 'error' "$DATA/sample.log" | wc -l


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "== 前 3 行 =="
sed -n '1,3p' "$DATA/sample.log"
echo "== 只打印 ERROR 行 =="
sed -n '/ERROR/p' "$DATA/sample.log" | head -3
echo "== 替换级别文字（只改每行第一处）=="
sed 's/INFO/INFO-OK/' "$DATA/sample.log" | head -2
echo "== 去掉耗时单位 =="
sed -E 's/([0-9]+)ms/\1/' "$DATA/sample.log" | head -2


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "服务             次数   平均毫秒"
awk '{
  ms = $7
  sub(/ms$/, "", ms)
  total[$4] += ms
  count[$4]++
}
END {
  for (name in total) {
    printf "%-16s %4d %8.1f\n", name, count[name], total[name] / count[name]
  }
}' "$DATA/sample.log" | sort


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "== 销售数据前 3 行 =="
head -3 "$DATA/sales.csv"
echo "== 各地区订单数 =="
cut -d, -f2 "$DATA/sales.csv" | tail -n +2 | sort | uniq -c | sort -rn
echo "== 总行数（含表头）=="
wc -l < "$DATA/sales.csv"


set -e
if [ -d assets ]; then DATA=assets; elif [ -d ../assets ]; then DATA=../assets; else DATA=.; fi
echo "地区         销售额"
awk -F, 'NR > 1 {
  total[$2] += $4 * $5
}
END {
  for (region in total) printf "%-8s %10.1f\n", region, total[region]
}' "$DATA/sales.csv" | sort -k2 -nr

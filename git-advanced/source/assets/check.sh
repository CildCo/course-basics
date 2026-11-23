#!/usr/bin/env bash
# 版本检查脚本：app.py 里出现故障标记时返回 1。
if grep -q "BROKEN = True" app.py; then
  echo "检查失败：发现故障标记"
  exit 1
fi
echo "检查通过"
exit 0

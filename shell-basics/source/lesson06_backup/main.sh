#!/usr/bin/env bash
set -euo pipefail

set -e
echo "当前时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "日期：$(date '+%F')"
echo "时间戳：$(date '+%Y%m%d-%H%M%S')"
echo "两天前：$(date -d '2 days ago' '+%F')"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
APP="$TMP/app"
mkdir -p "$APP/data" "$APP/logs"
echo "users" > "$APP/data/users.txt"
echo "orders" > "$APP/data/orders.txt"
echo "old log" > "$APP/logs/old.log"
echo "new log" > "$APP/logs/new.log"
touch -d '15 days ago' "$APP/logs/old.log"
touch -d '1 day ago' "$APP/data/users.txt"
echo "== 最近 2 天修改 =="
find "$APP" -type f -mtime -2
echo "== 超过 10 天未修改 =="
find "$APP" -type f -mtime +10
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/app/data"
echo "用户数据" > "$TMP/app/data/users.txt"
echo "配置" > "$TMP/app/settings.ini"
tar -czf "$TMP/app-backup.tar.gz" -C "$TMP/app" .
echo "== 压缩包内容 =="
tar -tzf "$TMP/app-backup.tar.gz"
ls -lh "$TMP/app-backup.tar.gz"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
APP="$TMP/app"
BACKUP="$TMP/backup"
mkdir -p "$APP/data" "$APP/logs" "$BACKUP"
echo "用户数据" > "$APP/data/users.txt"
echo "订单数据" > "$APP/data/orders.txt"
echo "访问日志" > "$APP/logs/access.log"
cat > "$TMP/backup.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${1:?请传入应用目录}"
BACKUP_DIR="${2:?请传入备份目录}"
STAMP="${3:-$(date '+%Y%m%d-%H%M%S')}"
mkdir -p "$BACKUP_DIR"
ARCHIVE="$BACKUP_DIR/app-$STAMP.tar.gz"
tar -czf "$ARCHIVE" -C "$APP_DIR" .
SIZE=$(du -h "$ARCHIVE" | cut -f1)
echo "$(date '+%F %T') 备份完成 $(basename "$ARCHIVE") 大小 $SIZE" >> "$BACKUP_DIR/backup.log"
printf '已生成：%s（%s）\n' "$(basename "$ARCHIVE")" "$SIZE"
SCRIPT
bash "$TMP/backup.sh" "$APP" "$BACKUP" 20261024-020000
bash "$TMP/backup.sh" "$APP" "$BACKUP" 20261025-020000
echo "== 备份目录 =="
ls -1 "$BACKUP"
echo "== 运行日志 =="
cat "$BACKUP/backup.log"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
APP="$TMP/app"
BACKUP="$TMP/backup"
mkdir -p "$APP" "$BACKUP"
echo "v1" > "$APP/data.txt"
run_backup() {
  local stamp="$1"
  tar -czf "$BACKUP/app-$stamp.tar.gz" -C "$APP" .
  echo "$(date '+%F %T') 模拟定时任务 $stamp 完成" >> "$BACKUP/backup.log"
}
echo "== 模拟 cron 连续三天触发 =="
for stamp in 20261023-020000 20261024-020000 20261025-020000; do
  run_backup "$stamp"
done
cat "$BACKUP/backup.log"
echo "== crontab 配置示例 =="
echo "0 2 * * * /opt/app/backup.sh /opt/app /backup >> /backup/cron.log 2>&1"
rm -rf "$TMP"


set -e
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
BACKUP="$TMP/backup"
mkdir -p "$BACKUP"
touch "$BACKUP/app-20261010-020000.tar.gz" "$BACKUP/app-20261024-020000.tar.gz"
touch -d '15 days ago' "$BACKUP/app-20261010-020000.tar.gz"
touch -d '1 day ago' "$BACKUP/app-20261024-020000.tar.gz"
echo "== 删除前 =="
ls -1 "$BACKUP"
echo "== 删除 10 天前的备份 =="
find "$BACKUP" -name 'app-*.tar.gz' -mtime +10 -print -delete
echo "== 删除后 =="
ls -1 "$BACKUP"
rm -rf "$TMP"

from pathlib import Path
import re


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


log_path = data_path("app.log")
lines = log_path.read_text(encoding="utf-8").splitlines()
print("日志行数：", len(lines))
print("第一行：", lines[0])
print("最后一行：", lines[-1])


log_pattern = re.compile(
    r'^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '
    r'(?P<level>INFO|WARN|ERROR) '
    r'\[(?P<service>[a-z-]+)\] '
    r'user=(?P<user>u\d+) '
    r'ip=(?P<ip>\d{1,3}(?:\.\d{1,3}){3}) '
    r'order=(?P<order>\d+) '
    r'duration=(?P<duration>\d+)ms '
    r'msg="(?P<msg>[^"]*)"$'
)

records = []
bad_lines = []
for line in lines:
    match = log_pattern.match(line)
    if match:
        row = match.groupdict()
        row["duration"] = int(row["duration"])
        records.append(row)
    else:
        bad_lines.append(line)

print("解析成功：", len(records), "条")
print("解析失败：", len(bad_lines), "条")
print("第一条记录：", records[0])


from collections import Counter, defaultdict

level_counts = Counter(row["level"] for row in records)
service_counts = Counter(row["service"] for row in records)
print("按级别统计：", dict(level_counts))
print("按服务统计：", dict(service_counts))

duration_by_service = defaultdict(list)
for row in records:
    duration_by_service[row["service"]].append(row["duration"])
print("各服务平均耗时：")
for service in sorted(duration_by_service):
    values = duration_by_service[service]
    print(f"  {service:<18} {sum(values) / len(values):.0f}ms（{len(values)} 条）")

print("耗时 TOP 5：")
for row in sorted(records, key=lambda item: item["duration"], reverse=True)[:5]:
    print(f'  {row["duration"]:>4}ms  {row["service"]:<18} {row["msg"]}')

print("ERROR 明细：")
for row in records:
    if row["level"] == "ERROR":
        print(f'  {row["ts"]}  {row["service"]}  order={row["order"]}  {row["msg"]}')


import csv

out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)
log_csv = out_dir / "app_log.csv"
fieldnames = ["ts", "level", "service", "user", "ip", "order", "duration", "msg"]

with log_csv.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print("已写入：", log_csv.name, "，行数：", len(records))
print("表头：", log_csv.read_text(encoding="utf-8").splitlines()[0])
print("示例：", log_csv.read_text(encoding="utf-8").splitlines()[1])


invoice_text = data_path("invoices.txt").read_text(encoding="utf-8")
blocks = [block.strip() for block in re.split(r"\n\s*\n", invoice_text) if block.strip()]
print("发票段数：", len(blocks))
print("第一段：")
print(blocks[0])


def field(block, labels):
    pattern = r"(?:" + "|".join(re.escape(label) for label in labels) + r")\s*[:：]\s*(.+)"
    match = re.search(pattern, block)
    return match.group(1).strip() if match else ""


invoices = []
for block in blocks:
    invoice_no = field(block, ["发票号码", "发票号"])
    date_text = field(block, ["开票日期", "日期"])
    buyer = field(block, ["购买方", "购方"])
    tax_id = field(block, ["纳税人识别号", "税号"])
    amount = float(field(block, ["金额（元）", "金额"]).replace(",", ""))
    rate_text = field(block, ["税率"])
    rate = float(rate_text.rstrip("%")) / 100
    tax = float(field(block, ["税额"]).replace(",", ""))

    date_norm = re.sub(r"[年月/]", "-", date_text).rstrip("日")
    expected_tax = round(amount * rate, 2)
    check = "一致" if abs(expected_tax - tax) < 0.02 else f"差异 {tax - expected_tax:.2f}"

    invoices.append(
        {
            "invoice_no": invoice_no,
            "date": date_norm,
            "buyer": buyer,
            "tax_id": tax_id,
            "amount": amount,
            "rate_text": rate_text,
            "rate": rate,
            "tax": tax,
            "tax_check": check,
        }
    )

for invoice in invoices:
    print(invoice)


invoice_csv = out_dir / "invoices.csv"
invoice_fields = [
    "invoice_no", "date", "buyer", "tax_id",
    "amount", "rate_text", "rate", "tax", "tax_check",
]
with invoice_csv.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=invoice_fields)
    writer.writeheader()
    writer.writerows(invoices)

summary = defaultdict(lambda: {"count": 0, "amount": 0.0, "tax": 0.0})
for invoice in invoices:
    bucket = summary[invoice["rate_text"]]
    bucket["count"] += 1
    bucket["amount"] += invoice["amount"]
    bucket["tax"] += invoice["tax"]

print("按税率汇总：")
for rate_text in sorted(summary):
    bucket = summary[rate_text]
    print(
        f"  {rate_text:>4}  {bucket['count']} 张  "
        f"金额 {bucket['amount']:>10.2f}  税额 {bucket['tax']:>9.2f}"
    )
print("合计金额：", round(sum(item["amount"] for item in invoices), 2))
print("合计税额：", round(sum(item["tax"] for item in invoices), 2))
print("已写入：", invoice_csv.name)

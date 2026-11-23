from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import numpy as np
import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

orders = pd.read_csv(
    data_path("orders.csv"),
    dtype={"customer_id": "string", "product_id": "string", "order_date": "string"},
)
customers = pd.read_csv(data_path("customers.csv"), dtype="string")
products = pd.read_csv(data_path("products.csv"), dtype="string")

orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="coerce")
orders["amount"] = pd.to_numeric(orders["amount"], errors="coerce")
print("订单表:", orders.shape, "客户表:", customers.shape, "商品表:", products.shape)


def build_findings(orders, customers, products, as_of):
    regions = ["华东", "华南", "华北", "西南"]
    levels = ["普通", "银卡", "金卡"]
    statuses = ["已完成", "已取消", "退款"]
    findings = []

    def add(table, rule, severity, failed):
        findings.append({"table": table, "rule": rule, "severity": severity, "failed": int(failed)})

    order_dates = pd.to_datetime(orders["order_date"], errors="coerce", format="mixed")
    expected = (orders["quantity"] * orders["unit_price"]).round(2)
    product_price = pd.to_numeric(products["unit_price"], errors="coerce")

    add("orders", "order_id 非空", "致命", orders["order_id"].isna().sum())
    add("orders", "order_id 唯一", "致命", orders["order_id"].duplicated().sum())
    add("orders", "customer_id 非空", "致命", orders["customer_id"].isna().sum())
    add("orders", "product_id 非空", "致命", orders["product_id"].isna().sum())
    add("orders", "customer_id 外键存在", "致命", (orders["customer_id"].notna() & ~orders["customer_id"].isin(customers["customer_id"])).sum())
    add("orders", "product_id 外键存在", "致命", (orders["product_id"].notna() & ~orders["product_id"].isin(products["product_id"])).sum())
    add("orders", "金额一致", "致命", ((orders["amount"] - expected).abs() > 0.01).sum())
    add("orders", "order_date 可解析", "致命", order_dates.isna().sum())
    add("orders", "quantity 在 1~99", "警告", (~orders["quantity"].between(1, 99)).sum())
    add("orders", "status 在允许集合", "警告", (~orders["status"].isin(statuses)).sum())
    add("orders", "order_date 不晚于统计日", "警告", (order_dates > as_of).sum())
    add("customers", "customer_id 唯一", "致命", customers["customer_id"].duplicated().sum())
    add("customers", "region 在允许集合", "警告", (~customers["region"].isin(regions)).sum())
    add("customers", "level 在允许集合", "警告", (~customers["level"].isin(levels)).sum())
    add("customers", "signup_date 非空", "警告", customers["signup_date"].isna().sum())
    add("products", "product_id 唯一", "致命", products["product_id"].duplicated().sum())
    add("products", "unit_price 在 0.01~100000", "警告", (~product_price.between(0.01, 100000)).sum())
    add("products", "name 非空", "警告", products["name"].isna().sum())
    return pd.DataFrame(findings)


as_of = pd.Timestamp("2026-10-01")
report = build_findings(orders, customers, products, as_of)
report["status"] = np.where(report["failed"] == 0, "通过", "未通过")
report["severity_order"] = report["severity"].map({"致命": 0, "警告": 1})
report = report.sort_values(["severity_order", "table", "rule"]).drop(columns="severity_order").reset_index(drop=True)

summary = report.groupby("severity", as_index=False).agg(
    规则数=("rule", "count"),
    未通过=("status", lambda values: int((values == "未通过").sum())),
    问题行数=("failed", "sum"),
)
print(summary.to_string(index=False))
print()
print(report.to_string(index=False))


path = out / "quality_report.csv"
report.to_csv(path, index=False, encoding="utf-8-sig")

fatal_failed = int(((report["severity"] == "致命") & (report["status"] == "未通过")).sum())
warning_failed = int(((report["severity"] == "警告") & (report["status"] == "未通过")).sum())
print("已写入:", path.name, "共", len(report), "条规则")
print("致命未通过:", fatal_failed, "条；警告未通过:", warning_failed, "条")


again = build_findings(orders, customers, products, as_of)
again["status"] = np.where(again["failed"] == 0, "通过", "未通过")

key = ["table", "rule", "severity", "failed", "status"]
report_key = report[key].sort_values(["table", "rule"]).reset_index(drop=True)
again_key = again[key].sort_values(["table", "rule"]).reset_index(drop=True)

fingerprint = int(pd.util.hash_pandas_object(report_key.astype(str).agg("|".join, axis=1), index=False).sum())
print("两次运行结果一致:", report_key.equals(again_key))
print("规则报告指纹:", fingerprint)
print("固定统计日:", as_of.date())

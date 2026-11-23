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


AS_OF = pd.Timestamp("2026-10-01")
REGIONS = ["华东", "华南", "华北", "西南", "未知"]
LEVELS = ["普通", "银卡", "金卡"]
STATUSES = ["已完成", "已取消", "退款"]

RULES = [
    {"table": "orders", "rule": "order_id 非空", "kind": "not_null", "column": "order_id", "severity": "致命"},
    {"table": "orders", "rule": "order_id 唯一", "kind": "unique", "column": "order_id", "severity": "致命"},
    {"table": "orders", "rule": "customer_id 非空", "kind": "not_null", "column": "customer_id", "severity": "致命"},
    {"table": "orders", "rule": "product_id 非空", "kind": "not_null", "column": "product_id", "severity": "致命"},
    {"table": "orders", "rule": "customer_id 外键存在", "kind": "fk", "column": "customer_id", "dim": "customers", "dim_key": "customer_id", "severity": "致命"},
    {"table": "orders", "rule": "product_id 外键存在", "kind": "fk", "column": "product_id", "dim": "products", "dim_key": "product_id", "severity": "致命"},
    {"table": "orders", "rule": "金额等于数量乘单价", "kind": "amount", "severity": "致命"},
    {"table": "orders", "rule": "order_date 可解析", "kind": "date_parse", "column": "order_date", "severity": "致命"},
    {"table": "orders", "rule": "quantity 在 1~99", "kind": "range", "column": "quantity", "min": 1, "max": 99, "severity": "警告"},
    {"table": "orders", "rule": "status 在允许集合", "kind": "in_set", "column": "status", "values": STATUSES, "severity": "警告"},
    {"table": "orders", "rule": "order_date 不晚于统计日", "kind": "freshness", "column": "order_date", "severity": "警告"},
    {"table": "customers", "rule": "customer_id 唯一", "kind": "unique", "column": "customer_id", "severity": "致命"},
    {"table": "customers", "rule": "region 在允许集合", "kind": "in_set", "column": "region", "values": REGIONS, "severity": "警告"},
    {"table": "customers", "rule": "level 在允许集合", "kind": "in_set", "column": "level", "values": LEVELS, "severity": "警告"},
    {"table": "customers", "rule": "signup_date 非空", "kind": "not_null", "column": "signup_date", "severity": "警告"},
    {"table": "products", "rule": "product_id 唯一", "kind": "unique", "column": "product_id", "severity": "致命"},
    {"table": "products", "rule": "unit_price 在 0.01~100000", "kind": "range", "column": "unit_price", "min": 0.01, "max": 100000, "severity": "警告"},
    {"table": "products", "rule": "name 非空", "kind": "not_null", "column": "name", "severity": "警告"},
]

print("规则条数:", len(RULES))
print("致命规则:", sum(rule["severity"] == "致命" for rule in RULES))
print("警告规则:", sum(rule["severity"] == "警告" for rule in RULES))


def failure_mask(tables, rule):
    frame = tables[rule["table"]]
    kind = rule["kind"]

    if kind == "not_null":
        return frame[rule["column"]].isna()
    if kind == "unique":
        return frame[rule["column"]].duplicated()
    if kind == "in_set":
        return ~frame[rule["column"]].isin(rule["values"])
    if kind == "range":
        numeric = pd.to_numeric(frame[rule["column"]], errors="coerce")
        return numeric.isna() | (numeric < rule["min"]) | (numeric > rule["max"])
    if kind == "fk":
        values = frame[rule["column"]]
        return values.notna() & ~values.isin(tables[rule["dim"]][rule["dim_key"]])
    if kind == "amount":
        expected = (frame["quantity"] * frame["unit_price"]).round(2)
        return (frame["amount"] - expected).abs() > 0.01
    if kind == "date_parse":
        return pd.to_datetime(frame[rule["column"]], errors="coerce", format="mixed").isna()
    if kind == "freshness":
        dates = pd.to_datetime(frame[rule["column"]], errors="coerce", format="mixed")
        return dates > AS_OF
    raise ValueError(f"未知规则类型：{kind}")


def run_gate(tables):
    rows = []
    for rule in RULES:
        failed = int(failure_mask(tables, rule).sum())
        rows.append(
            {
                "table": rule["table"],
                "rule": rule["rule"],
                "severity": rule["severity"],
                "failed": failed,
                "status": "通过" if failed == 0 else "未通过",
            }
        )
    return pd.DataFrame(rows)


tables = {"orders": orders, "customers": customers, "products": products}
gate = run_gate(tables)

fatal_rules = int(((gate["severity"] == "致命") & (gate["status"] == "未通过")).sum())
warning_rules = int(((gate["severity"] == "警告") & (gate["status"] == "未通过")).sum())
fatal_rows = int(gate.loc[(gate["severity"] == "致命") & (gate["status"] == "未通过"), "failed"].sum())
warning_rows = int(gate.loc[(gate["severity"] == "警告") & (gate["status"] == "未通过"), "failed"].sum())

decision = "放行" if fatal_rules == 0 and warning_rows <= 20 else "拦截"
print("致命未通过规则:", fatal_rules, "条；命中行数:", fatal_rows)
print("警告未通过规则:", warning_rules, "条；命中行数:", warning_rows)
print("门禁结论:", decision)
print()
print(gate[gate["status"] == "未通过"].to_string(index=False))


clean_customers = customers.drop_duplicates(subset="customer_id", keep="last").copy()
clean_customers["region"] = clean_customers["region"].str.strip().replace("", pd.NA).fillna("未知")

clean_products = products.drop_duplicates(subset="product_id", keep="first").copy()

clean_orders = orders.drop_duplicates().drop_duplicates(subset="order_id", keep="last").copy()
clean_orders["quantity"] = pd.to_numeric(clean_orders["quantity"], errors="coerce")
clean_orders["unit_price"] = pd.to_numeric(clean_orders["unit_price"], errors="coerce")
clean_orders["amount"] = (clean_orders["quantity"] * clean_orders["unit_price"]).round(2)
clean_orders["_date"] = pd.to_datetime(clean_orders["order_date"], errors="coerce", format="mixed")

keep = (
    clean_orders["customer_id"].notna()
    & clean_orders["product_id"].notna()
    & clean_orders["customer_id"].isin(clean_customers["customer_id"])
    & clean_orders["product_id"].isin(clean_products["product_id"])
    & clean_orders["quantity"].between(1, 99)
    & clean_orders["_date"].notna()
    & (clean_orders["_date"] <= AS_OF)
    & clean_orders["status"].isin(STATUSES)
)
clean_orders = clean_orders[keep].drop(columns="_date")

print("订单行数:", len(orders), "->", len(clean_orders))
print("客户行数:", len(customers), "->", len(clean_customers))
print("商品行数:", len(products), "->", len(clean_products))


clean_tables = {"orders": clean_orders, "customers": clean_customers, "products": clean_products}
clean_gate = run_gate(clean_tables)

clean_fatal = int(((clean_gate["severity"] == "致命") & (clean_gate["status"] == "未通过")).sum())
clean_warning_rows = int(clean_gate.loc[(clean_gate["severity"] == "警告") & (clean_gate["status"] == "未通过"), "failed"].sum())
decision = "放行" if clean_fatal == 0 and clean_warning_rows <= 20 else "拦截"

print("修复后致命未通过:", clean_fatal, "条")
print("修复后警告命中行数:", clean_warning_rows)
print("门禁结论:", decision)
print()
print(clean_gate[clean_gate["status"] == "未通过"].to_string(index=False))


path = out / "quality_gate_report.csv"
clean_gate.to_csv(path, index=False, encoding="utf-8-sig")

summary_text = "\n".join(
    [
        "订单数据质量门禁",
        f"统计日: {AS_OF.date()}",
        f"规则总数: {len(clean_gate)}",
        f"致命未通过: {clean_fatal}",
        f"警告命中行数: {clean_warning_rows}",
        f"结论: {decision}",
        "",
        "修复说明: 删除完全重复和主键重复行；丢弃缺失外键、孤儿外键、非法数量、非法日期和非法状态的行；金额按数量乘单价重算；客户地区统一去空格并允许“未知”兜底。",
    ]
)
(out / "quality_gate_summary.txt").write_text(summary_text + "\n", encoding="utf-8")

print(summary_text)
print()
print("报告文件:", path.name, "| 汇总文件: quality_gate_summary.txt")

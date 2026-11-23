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
orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="coerce")
orders["amount"] = pd.to_numeric(orders["amount"], errors="coerce")
print("订单表:", orders.shape)


rules = [
    {"rule_id": "R01", "table": "orders", "column": "order_id", "kind": "not_null", "params": {}, "severity": "致命"},
    {"rule_id": "R02", "table": "orders", "column": "order_id", "kind": "unique", "params": {}, "severity": "致命"},
    {"rule_id": "R03", "table": "orders", "column": "status", "kind": "in_set", "params": {"values": ["已完成", "已取消", "退款"]}, "severity": "警告"},
    {"rule_id": "R04", "table": "orders", "column": "quantity", "kind": "range", "params": {"min": 1, "max": 99}, "severity": "警告"},
    {"rule_id": "R05", "table": "orders", "column": "unit_price", "kind": "range", "params": {"min": 0.01, "max": 100000}, "severity": "警告"},
]
rule_table = pd.DataFrame(rules)
print(rule_table[["rule_id", "column", "kind", "severity"]].to_string(index=False))


def failed_mask(frame, kind, column, params):
    series = frame[column]
    if kind == "not_null":
        return series.isna()
    if kind == "unique":
        return series.duplicated(keep="first")
    if kind == "in_set":
        return ~series.isin(params["values"])
    if kind == "range":
        numeric = pd.to_numeric(series, errors="coerce")
        return numeric.isna() | (numeric < params["min"]) | (numeric > params["max"])
    raise ValueError(f"未知规则类型：{kind}")


def run_rules(frame, rules):
    rows = []
    for rule in rules:
        failed = int(failed_mask(frame, rule["kind"], rule["column"], rule["params"]).sum())
        rows.append(
            {
                "rule_id": rule["rule_id"],
                "column": rule["column"],
                "kind": rule["kind"],
                "severity": rule["severity"],
                "failed": failed,
                "passed": failed == 0,
            }
        )
    return pd.DataFrame(rows)


result = run_rules(orders, rules)
print(result.to_string(index=False))


extra = {
    "rule_id": "R06",
    "table": "orders",
    "column": "amount",
    "kind": "range",
    "params": {"min": 0.01, "max": 100000},
    "severity": "警告",
}
result2 = run_rules(orders, rules + [extra])
print(result2.tail(2).to_string(index=False))
print()
print("规则条数:", len(result2), "；执行器代码未改")

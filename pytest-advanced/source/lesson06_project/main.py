import json
import os
import sys
import tempfile
from pathlib import Path

import pytest


def data_path(name):
    here = Path.cwd().resolve()
    for base in (here, *here.parents):
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"找不到 assets/{name}")


def run_pytest(target, *args):
    target = Path(target)
    workdir = target if target.is_dir() else target.parent
    previous = Path.cwd()
    os.chdir(workdir)
    try:
        code = pytest.main([
            str(target),
            "-q",
            "--color=no",
            "--disable-warnings",
            "-p", "no:cacheprovider",
            "--import-mode=importlib",
            *args,
        ])
    finally:
        os.chdir(previous)
    print("退出码：", code)
    if int(code) != 0:
        raise RuntimeError(f"pytest 退出码：{code}")


orders = json.loads(data_path("orders.json").read_text(encoding="utf-8"))
project = tempfile.TemporaryDirectory(prefix="pytest-project-")
root = Path(project.name)
(root / "pytest.ini").write_text("[pytest]" + chr(10), encoding="utf-8")
sys.path.insert(0, str(root))
(root / "tests").mkdir()
(root / "orders.json").write_text(
    json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8"
)

(root / "pytest.ini").write_text("""[pytest]
markers =
    unit: 快速单元测试
    integration: 使用真实数据文件的集成测试
testpaths = tests
disable_test_id_escaping_and_forfeit_all_rights_to_community_support = True
""", encoding="utf-8")

(root / "pipeline.py").write_text("""import json
from datetime import date
from pathlib import Path


def today():
    return date.today().isoformat()


def load_orders(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("订单文件必须是数组")
    return rows


def clean_orders(rows):
    cleaned = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("status") != "paid":
            continue
        amount = row.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            continue
        if amount <= 0:
            continue
        customer = str(row.get("customer") or "").strip()
        if not customer:
            continue
        cleaned.append({**row, "customer": customer, "amount": float(amount)})
    return cleaned


def summarize(orders):
    by_customer = {}
    for order in orders:
        by_customer[order["customer"]] = round(
            by_customer.get(order["customer"], 0.0) + order["amount"], 2
        )
    total = round(sum(order["amount"] for order in orders), 2)
    return {
        "orderCount": len(orders),
        "totalRevenue": total,
        "averageOrder": round(total / len(orders), 2) if orders else 0.0,
        "byCustomer": dict(sorted(by_customer.items())),
    }


def build_report(source, target, run_date=None):
    report = summarize(clean_orders(load_orders(source)))
    report["generatedAt"] = run_date or today()
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report
""", encoding="utf-8")

(root / "conftest.py").write_text("""import json
from pathlib import Path

import pytest


@pytest.fixture
def raw_orders():
    return [
        {"order_id": "T1", "customer": "华东", "amount": 100, "status": "paid"},
        {"order_id": "T2", "customer": "华东", "amount": 0, "status": "paid"},
        {"order_id": "T3", "customer": "", "amount": 50, "status": "paid"},
        {"order_id": "T4", "customer": "华南", "amount": 30, "status": "refunded"},
        {"order_id": "T5", "customer": "华南", "amount": 20, "status": "paid"},
    ]


@pytest.fixture
def order_file(tmp_path, raw_orders):
    path = tmp_path / "orders.json"
    path.write_text(json.dumps(raw_orders, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def sample_file():
    return Path(__file__).parent / "orders.json"
""", encoding="utf-8")

(root / "tests" / "test_unit.py").write_text("""import pytest

import pipeline


@pytest.mark.unit
def test_clean_drops_invalid_rows(raw_orders):
    cleaned = pipeline.clean_orders(raw_orders)
    assert [row["order_id"] for row in cleaned] == ["T1", "T5"]


@pytest.mark.unit
def test_summarize(raw_orders):
    summary = pipeline.summarize(pipeline.clean_orders(raw_orders))
    assert summary == {
        "orderCount": 2,
        "totalRevenue": 120.0,
        "averageOrder": 60.0,
        "byCustomer": {"华东": 100.0, "华南": 20.0},
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "amount, status, expected",
    [
        (100, "paid", True),
        (0, "paid", False),
        (-1, "paid", False),
        (100, "refunded", False),
        ("100", "paid", False),
    ],
    ids=["正常", "零金额", "负数", "已退款", "金额是字符串"],
)
def test_keep_rule(amount, status, expected):
    row = {"order_id": "X", "customer": "华东", "amount": amount, "status": status}
    assert bool(pipeline.clean_orders([row])) is expected
""", encoding="utf-8")

(root / "tests" / "test_report.py").write_text("""import json

import pytest

import pipeline


@pytest.mark.unit
def test_build_report_writes_file(order_file, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "today", lambda: "2026-10-25")
    target = tmp_path / "report.json"
    report = pipeline.build_report(order_file, target)
    assert report["generatedAt"] == "2026-10-25"
    assert json.loads(target.read_text(encoding="utf-8")) == report


@pytest.mark.unit
def test_reports_are_isolated(order_file, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "today", lambda: "2026-10-25")
    first = pipeline.build_report(order_file, tmp_path / "a.json")
    second = pipeline.build_report(order_file, tmp_path / "b.json")
    assert first == second
    assert (tmp_path / "a.json").read_text(encoding="utf-8") != ""
""", encoding="utf-8")

(root / "tests" / "test_errors.py").write_text("""import json

import pytest

import pipeline


@pytest.mark.unit
def test_bad_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        pipeline.load_orders(path)


@pytest.mark.unit
def test_not_array(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="数组"):
        pipeline.load_orders(path)
""", encoding="utf-8")

(root / "tests" / "test_integration.py").write_text("""import pytest

import pipeline


@pytest.mark.integration
def test_sample_orders(sample_file, tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "today", lambda: "2026-10-25")
    target = tmp_path / "report.json"
    report = pipeline.build_report(sample_file, target)
    assert report == {
        "orderCount": 4,
        "totalRevenue": 326.4,
        "averageOrder": 81.6,
        "byCustomer": {"华东": 284.4, "华南": 42.0},
        "generatedAt": "2026-10-25",
    }
    assert target.exists()
""", encoding="utf-8")

print("原始订单数:", len(orders))
print(
    "状态分布:",
    {
        status: sum(1 for row in orders if row["status"] == status)
        for status in sorted({row["status"] for row in orders})
    },
)
print("测试工程结构:")
for path in sorted(root.rglob("*")):
    if path.is_file():
        print("-", path.relative_to(root).as_posix())


run_pytest(root, "-m", "unit")


class Collector:
    def __init__(self):
        self.tests = []

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.tests.append({
                "test": report.nodeid,
                "outcome": report.outcome,
                "duration": round(report.duration, 4),
            })


collector = Collector()
previous = Path.cwd()
os.chdir(root)
try:
    code = pytest.main([
        str(root),
        "-q",
        "--color=no",
        "--disable-warnings",
        "-p", "no:cacheprovider",
        "--import-mode=importlib",
    ], plugins=[collector])
finally:
    os.chdir(previous)

if int(code) != 0:
    raise RuntimeError(f"pytest 退出码：{code}")

summary = {
    "exitCode": code,
    "total": len(collector.tests),
    "passed": sum(item["outcome"] == "passed" for item in collector.tests),
    "failed": sum(item["outcome"] == "failed" for item in collector.tests),
    "tests": collector.tests,
}

output = Path("output") / "lesson06"
output.mkdir(parents=True, exist_ok=True)
report_path = output / "test-report.json"
report_path.write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("报告路径:", report_path)
print("汇总:", {key: summary[key] for key in ("exitCode", "total", "passed", "failed")})


print("测试文件:")
for path in sorted((root / "tests").glob("test_*.py")):
    print("-", path.relative_to(root).as_posix())

print("报告内容:")
print(report_path.read_text(encoding="utf-8"))
project.cleanup()

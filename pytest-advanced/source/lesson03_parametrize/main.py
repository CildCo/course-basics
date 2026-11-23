import json
import os
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


prices = json.loads(data_path("prices.json").read_text(encoding="utf-8"))
project = tempfile.TemporaryDirectory(prefix="pytest-param-")
root = Path(project.name)
(root / "pytest.ini").write_text("[pytest]" + chr(10), encoding="utf-8")
(root / "prices.json").write_text(
    json.dumps(prices, ensure_ascii=False, indent=2), encoding="utf-8"
)

(root / "test_param.py").write_text("""import json
from pathlib import Path

import pytest


def discount(amount, is_new=False):
    if amount < 0:
        raise ValueError("金额不能为负")
    return round(amount * 0.9, 2) if is_new else amount


@pytest.mark.parametrize(
    "amount, is_new, expected",
    [(100, False, 100), (100, True, 90), (20, True, 18)],
    ids=["原价", "新用户九折", "新用户小额"],
)
def test_discount(amount, is_new, expected):
    assert discount(amount, is_new) == expected


CASES = json.loads((Path(__file__).parent / "prices.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES["discount_cases"], ids=lambda case: case["name"])
def test_from_data(case):
    assert discount(case["amount"], case["is_new"]) == case["expected"]


@pytest.mark.parametrize("status", ["paid", "refunded"])
@pytest.mark.parametrize("amount", [0, 100])
def test_status_amount_matrix(status, amount):
    pairs = {("paid", 0), ("paid", 100), ("refunded", 0), ("refunded", 100)}
    assert (status, amount) in pairs


@pytest.mark.parametrize(
    "amount",
    [
        pytest.param(100, id="正常金额"),
        pytest.param(0, id="零金额"),
        pytest.param(200, id="演示跳过", marks=pytest.mark.skip(reason="这组数据暂不执行")),
    ],
)
def test_case_marks(amount):
    assert discount(amount) >= 0
""", encoding="utf-8")

print("数据文件: assets/prices.json")
print("用例数据:", json.dumps(prices["discount_cases"], ensure_ascii=False))
print("测试工程已创建")


run_pytest(root / "test_param.py")


(root / "test_indirect.py").write_text("""import pytest


@pytest.fixture
def account(request):
    return {"role": request.param, "can_export": request.param == "admin"}


@pytest.mark.parametrize("account", ["admin", "viewer"], indirect=True)
def test_permission(account):
    assert account["can_export"] is (account["role"] == "admin")
""", encoding="utf-8")

run_pytest(root / "test_indirect.py")
project.cleanup()

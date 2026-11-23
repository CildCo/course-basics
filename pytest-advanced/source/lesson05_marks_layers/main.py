import os
import tempfile
from pathlib import Path

import pytest


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


project = tempfile.TemporaryDirectory(prefix="pytest-marks-")
root = Path(project.name)

(root / "pytest.ini").write_text("""[pytest]
markers =
    unit: 不依赖外部资源，提交前运行
    integration: 组合多个模块或文件，合并前运行
    slow: 耗时较长，按需运行
""", encoding="utf-8")

(root / "test_layers.py").write_text("""import sys

import pytest


def retry(func, times=3):
    last_error = None
    for _ in range(times):
        try:
            return func()
        except ConnectionError as exc:
            last_error = exc
    raise last_error


@pytest.mark.unit
def test_math():
    assert 2 + 2 == 4


@pytest.mark.integration
def test_two_modules():
    rows = [{"amount": 10}, {"amount": 20}]
    assert sum(row["amount"] for row in rows) == 30


@pytest.mark.skip(reason="功能尚未实现")
def test_unfinished():
    assert False


@pytest.mark.skipif(sys.version_info < (3, 10), reason="需要 Python 3.10+")
def test_version_gate():
    assert sys.version_info >= (3, 10)


@pytest.mark.xfail(reason="已知浮点边界问题", strict=True)
def test_known_bug():
    assert 0.1 + 0.2 == 0.3


@pytest.mark.unit
def test_retry_until_success():
    state = {"calls": 0}

    def call():
        state["calls"] += 1
        if state["calls"] < 3:
            raise ConnectionError("暂时失败")
        return "ok"

    assert retry(call) == "ok"
    assert state["calls"] == 3
""", encoding="utf-8")

print("标记配置:")
print((root / "pytest.ini").read_text(encoding="utf-8").strip())
print("测试工程已创建")


run_pytest(root / "test_layers.py", "-m", "unit")


run_pytest(root / "test_layers.py")


run_pytest(root / "test_layers.py", "-m", "not integration")
project.cleanup()

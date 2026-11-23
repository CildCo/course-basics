import json
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


project = tempfile.TemporaryDirectory(prefix="pytest-scope-")
root = Path(project.name)
(root / "pytest.ini").write_text("[pytest]" + chr(10), encoding="utf-8")

(root / "conftest.py").write_text("""import json
from pathlib import Path

import pytest

EVENTS = []


def record(name):
    EVENTS.append(name)


@pytest.fixture(scope="session")
def session_ctx():
    record("session setup")
    yield {"name": "session"}
    record("session teardown")


@pytest.fixture(scope="module")
def module_ctx():
    record("module setup")
    yield {"seen": []}
    record("module teardown")


@pytest.fixture
def case_ctx():
    record("function setup")
    yield []
    record("function teardown")


def pytest_sessionfinish(session, exitstatus):
    target = Path(__file__).with_name("events.json")
    target.write_text(json.dumps(EVENTS, ensure_ascii=False, indent=2), encoding="utf-8")
""", encoding="utf-8")

(root / "test_scope.py").write_text("""def test_first(session_ctx, module_ctx, case_ctx):
    print("用例 1 拿到:", session_ctx["name"], module_ctx, case_ctx)


def test_second(session_ctx, module_ctx, case_ctx):
    print("用例 2 拿到:", module_ctx, case_ctx)


def test_third(module_ctx):
    print("用例 3 只依赖 module 和 session")
""", encoding="utf-8")

print("测试工程已创建")
print("文件:", sorted(path.name for path in root.iterdir()))


run_pytest(root, "-s")


events = json.loads((root / "events.json").read_text(encoding="utf-8"))
for index, event in enumerate(events, 1):
    print(f"{index:>2}. {event}")

print("session setup 次数:", events.count("session setup"))
print("module setup 次数:", events.count("module setup"))
print("function setup 次数:", events.count("function setup"))
project.cleanup()

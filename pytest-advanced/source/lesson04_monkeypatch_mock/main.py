import os
import sys
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


project = tempfile.TemporaryDirectory(prefix="pytest-mock-")
root = Path(project.name)
(root / "pytest.ini").write_text("[pytest]" + chr(10), encoding="utf-8")
sys.path.insert(0, str(root))

(root / "settings.py").write_text("""import os


def endpoint():
    return os.environ.get("PYTEST_ADVANCED_ENDPOINT", "https://api.example.com")


def mode():
    return os.environ.get("PYTEST_ADVANCED_MODE", "prod")
""", encoding="utf-8")

(root / "test_env.py").write_text("""import settings


def test_defaults(monkeypatch):
    monkeypatch.delenv("PYTEST_ADVANCED_ENDPOINT", raising=False)
    monkeypatch.delenv("PYTEST_ADVANCED_MODE", raising=False)
    assert settings.endpoint() == "https://api.example.com"
    assert settings.mode() == "prod"


def test_env_override(monkeypatch):
    monkeypatch.setenv("PYTEST_ADVANCED_ENDPOINT", "https://test.local")
    monkeypatch.setenv("PYTEST_ADVANCED_MODE", "test")
    assert settings.endpoint() == "https://test.local"
    assert settings.mode() == "test"


def test_env_restored():
    assert settings.endpoint() == "https://api.example.com"
    assert settings.mode() == "prod"


def test_setattr(monkeypatch):
    monkeypatch.setattr(settings, "endpoint", lambda: "https://fake.local")
    assert settings.endpoint() == "https://fake.local"


def test_setattr_restored():
    assert settings.endpoint() == "https://api.example.com"
""", encoding="utf-8")

print("测试工程已创建")
print("文件:", sorted(path.name for path in root.iterdir()))


run_pytest(root / "test_env.py")


(root / "weather.py").write_text("""def fetch(city):
    raise RuntimeError("测试中不应访问网络")


def report(city):
    return f"{city} {fetch(city)} 度"
""", encoding="utf-8")

(root / "test_mock.py").write_text("""from unittest.mock import MagicMock, patch

import pytest

import weather


def test_report_uses_mock():
    with patch.object(weather, "fetch", return_value=26) as fake:
        assert weather.report("杭州") == "杭州 26 度"
        fake.assert_called_once_with("杭州")


def test_timeout_branch():
    with patch.object(weather, "fetch", side_effect=TimeoutError("超时")):
        with pytest.raises(TimeoutError):
            weather.report("杭州")


def test_magicmock_contract():
    client = MagicMock()
    client.get.return_value = {"ok": True}
    response = client.get("/health")
    assert response["ok"] is True
    client.get.assert_called_once_with("/health")
""", encoding="utf-8")

run_pytest(root / "test_mock.py")


import weather

try:
    weather.report("杭州")
except RuntimeError as exc:
    print("mock 只在测试内生效，真实函数仍然拒绝联网：", exc)
project.cleanup()

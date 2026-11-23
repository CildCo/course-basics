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


project = tempfile.TemporaryDirectory(prefix="pytest-tmp-")
root = Path(project.name)
(root / "pytest.ini").write_text("[pytest]" + chr(10), encoding="utf-8")

(root / "conftest.py").write_text("""import json
from pathlib import Path

import pytest


def record_cleanup(name):
    target = Path(__file__).with_name("cleanup.json")
    data = []
    if target.exists():
        data = json.loads(target.read_text(encoding="utf-8"))
    data.append(name)
    target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def settings(tmp_path):
    data = {"endpoint": "https://example.invalid", "batch": 2}
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def client(settings, tmp_path):
    log = tmp_path / "client.log"
    log.write_text("", encoding="utf-8")
    yield {
        "endpoint": settings["endpoint"],
        "batch": settings["batch"],
        "log": log,
    }
    log.unlink()
    record_cleanup("client")
""", encoding="utf-8")

(root / "test_di.py").write_text("""import json
from pathlib import Path


def test_settings_injected(client):
    assert client["endpoint"].startswith("https://")
    assert client["batch"] == 2


def test_tmp_path_unique_a(tmp_path):
    (tmp_path / "cache.txt").write_text("a", encoding="utf-8")
    print("第一个临时目录:", tmp_path.name)


def test_tmp_path_unique_b(tmp_path):
    assert not (tmp_path / "cache.txt").exists()
    print("第二个临时目录:", tmp_path.name)


def test_cleanup_happened():
    target = Path(__file__).with_name("cleanup.json")
    assert "client" in json.loads(target.read_text(encoding="utf-8"))
""", encoding="utf-8")

print("测试工程已创建")
print("文件:", sorted(path.name for path in root.iterdir()))


run_pytest(root, "-s")


cleanup = json.loads((root / "cleanup.json").read_text(encoding="utf-8"))
print("清理记录:", cleanup)
print("说明: client fixture 在 yield 之后删除了日志文件")
project.cleanup()

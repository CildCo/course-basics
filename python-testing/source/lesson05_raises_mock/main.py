import subprocess
import sys
from pathlib import Path

output = Path("output") / "lesson05"
output.mkdir(parents=True, exist_ok=True)

def run_pytest():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--disable-warnings"],
        cwd=output,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [line for line in result.stdout.splitlines() if "passed" in line or "failed" in line or "error" in line]
    print(lines[-1].split(" in ")[0] if lines else result.stdout.strip())
    if result.returncode != 0:
        print(result.stdout)
    return result.returncode


(output / "test_raises.py").write_text(
    "import pytest\n\n"
    "def parse(text):\n    return int(text)\n\n"
    "def test_parse_ok():\n    assert parse('18') == 18\n\n"
    "def test_parse_error():\n    with pytest.raises(ValueError):\n        parse('abc')\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())


(output / "weather.py").write_text(
    "def fetch_temperature():\n    raise RuntimeError('不应在测试里访问网络')\n\n"
    "def report():\n    return f'温度 {fetch_temperature()} 度'\n",
    encoding="utf-8",
)
(output / "test_mock.py").write_text(
    "import weather\n\n"
    "def test_report(monkeypatch):\n"
    "    monkeypatch.setattr(weather, 'fetch_temperature', lambda: 26)\n"
    "    assert weather.report() == '温度 26 度'\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())

import subprocess
import sys
from pathlib import Path

output = Path("output") / "lesson04"
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


(output / "conftest.py").write_text(
    "import pytest\n\n"
    "@pytest.fixture\ndef numbers():\n    return [1, 2, 3]\n",
    encoding="utf-8",
)
(output / "test_fixture.py").write_text(
    "def test_sum(numbers):\n    assert sum(numbers) == 6\n\n"
    "def test_length(numbers):\n    assert len(numbers) == 3\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())


(output / "test_param.py").write_text(
    "import pytest\n\n"
    "@pytest.mark.parametrize('value, expected', [(1, 2), (2, 4), (3, 6)])\n"
    "def test_double(value, expected):\n    assert value * 2 == expected\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())

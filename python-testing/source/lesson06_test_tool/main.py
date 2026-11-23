import subprocess
import sys
from pathlib import Path

output = Path("output") / "lesson06"
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


(output / "calculator.py").write_text(
    "def add(a, b):\n    return a + b\n\n"
    "def divide(a, b):\n    if b == 0:\n        raise ValueError('除数不能为 0')\n    return a / b\n",
    encoding="utf-8",
)
print((output / "calculator.py").read_text(encoding="utf-8"))


(output / "test_calculator.py").write_text(
    "import pytest\n\n"
    "from calculator import add, divide\n\n"
    "def test_add():\n    assert add(2, 3) == 5\n\n"
    "def test_divide():\n    assert divide(10, 2) == 5\n\n"
    "def test_divide_zero():\n    with pytest.raises(ValueError):\n        divide(1, 0)\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())

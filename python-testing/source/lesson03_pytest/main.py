import subprocess
import sys
from pathlib import Path

output = Path("output") / "lesson03"
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


(output / "calc.py").write_text(
    "def add(a, b):\n    return a + b\n",
    encoding="utf-8",
)
(output / "test_calc.py").write_text(
    "from calc import add\n\n"
    "def test_add():\n    assert add(2, 3) == 5\n\n"
    "def test_add_negative():\n    assert add(-1, 1) == 0\n",
    encoding="utf-8",
)
print("files:", sorted(path.name for path in output.glob("*.py")))


print("退出码：", run_pytest())


(output / "test_calc.py").write_text(
    "from calc import add\n\n"
    "def test_add():\n    assert add(2, 3) == 6\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())


(output / "test_calc.py").write_text(
    "from calc import add\n\n"
    "def test_add():\n    assert add(2, 3) == 5\n",
    encoding="utf-8",
)
print("退出码：", run_pytest())

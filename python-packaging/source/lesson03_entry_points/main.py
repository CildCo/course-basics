import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import os
import shutil
import subprocess
import sys


def data_path(name):
    here = Path.cwd()
    for base in [here, *here.parents]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


OUTPUT = Path.cwd() / "output"
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir(parents=True)
source = data_path("mini_tool")
print("素材项目：", source)
print("文件数：", len([p for p in source.rglob("*") if p.is_file()]))


import tomllib
from pathlib import Path
import shutil


if __name__ == "__main__":
    project = OUTPUT / "wordmeter_project"
    shutil.copytree(source, project)
    data = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    for command, target in data["project"]["scripts"].items():
        module, function = target.split(":")
        print(f"命令：{command}")
        print(f"模块：{module}")
        print(f"函数：{function}")


def run(args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, *args],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("$", " ".join(args))
    print(result.stdout.strip())
    if result.stderr.strip():
        print("[stderr]", result.stderr.strip())
    print("退出码：", result.returncode)
    print()
    return result


if __name__ == "__main__":
    sample = data_path("sample.txt")
    run(["-m", "wordmeter", str(sample)])
    run(["-m", "wordmeter", str(sample), "--json"])
    run(["-m", "wordmeter", "--version"])


from pathlib import Path


if __name__ == "__main__":
    script = OUTPUT / "wordmeter_script.py"
    script.write_text(
        "import sys\n"
        "from wordmeter.cli import main\n"
        "raise SystemExit(main())\n",
        encoding="utf-8",
    )
    sample = data_path("sample.txt")
    run([str(script), str(sample)])
    run([str(script), str(sample), "--json"])


if __name__ == "__main__":
    run(["-m", "wordmeter", "--help"])


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

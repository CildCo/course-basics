import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

project = data_path("pipeline-demo")
print("示例项目:", project.name)
print("项目文件:")
for path in sorted(project.rglob("*")):
    if path.is_file():
        print("  ", path.relative_to(project).as_posix())


STEPS = [
    ("检查", [sys.executable, "-m", "compileall", "-q", "src", "tests"]),
    ("测试", [sys.executable, "-m", "pytest", "--color=no"]),
    (
        "构建",
        [
            sys.executable, "-m", "pip", "wheel", ".",
            "--no-deps", "--no-build-isolation", "--no-index",
            "--no-cache-dir", "-w", "dist",
        ],
    ),
]

with tempfile.TemporaryDirectory(prefix="cicd-local-") as tmp:
    work = Path(tmp) / "pipeline-demo"
    shutil.copytree(project, work)

    summary = []
    for name, command in STEPS:
        proc = subprocess.run(
            command,
            cwd=work,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        summary.append((name, proc.returncode))
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        tail = lines[-1] if lines else ""
        print(f"{name} 退出码 {proc.returncode}  {tail}")

    wheels = sorted((work / "dist").glob("*.whl"))
    print("\n阶段结果:")
    for name, code in summary:
        status = "通过" if code == 0 else "失败"
        print(f"  {name:<4} {status} (exit={code})")
    print("产物:", [item.name for item in wheels])


with tempfile.TemporaryDirectory(prefix="cicd-fail-") as tmp:
    work = Path(tmp) / "pipeline-demo"
    shutil.copytree(project, work)
    target = work / "src" / "pipeline_demo" / "release.py"
    source = target.read_text(encoding="utf-8")
    target.write_text(
        source.replace('return f"{major + 1}.0.0"', 'return f"{major + 2}.0.0"'),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--color=no"],
        cwd=work,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    print("故意改坏主版本递增后：")
    print("  pytest 退出码:", proc.returncode)
    print("  最后一行:", lines[-1])
    print("  构建阶段:", "不执行" if proc.returncode != 0 else "继续执行")

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import hashlib
import json
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

project = data_path("pipeline-demo")
out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

print("项目:", project.name)
print("输出目录:", out.name)


script_text = r'''"""本地流水线：检查、测试、构建 wheel 并生成制品清单。"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_step(name, command, cwd):
    proc = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(f"[{name}] exit={proc.returncode}")
    if proc.stdout.strip():
        print(proc.stdout.strip()[-1200:])
    if proc.returncode != 0 and proc.stderr.strip():
        print(proc.stderr.strip()[-1200:])
    return proc.returncode


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="运行本地 CI 流水线")
    parser.add_argument("--project", required=True, help="示例项目目录")
    parser.add_argument("--output", default="output", help="输出目录")
    args = parser.parse_args()

    source = Path(args.project).resolve()
    output = Path(args.output).resolve()
    artifacts_dir = output / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cicd-build-") as tmp:
        work = Path(tmp) / source.name
        shutil.copytree(source, work)
        steps = [
            ("check", [sys.executable, "-m", "compileall", "-q", "src", "tests"]),
            ("test", [sys.executable, "-m", "pytest", "--color=no"]),
            (
                "build",
                [
                    sys.executable, "-m", "pip", "wheel", ".",
                    "--no-deps", "--no-build-isolation", "--no-index",
                    "--no-cache-dir", "-w", "dist",
                ],
            ),
        ]
        for name, command in steps:
            if run_step(name, command, work) != 0:
                print(f"流水线在 {name} 阶段停止")
                return 1

        wheel = sorted((work / "dist").glob("*.whl"))[-1]
        target = artifacts_dir / wheel.name
        shutil.copy2(wheel, target)

    manifest = {
        "project": source.name,
        "artifact": target.name,
        "size": target.stat().st_size,
        "sha256": sha256(target),
        "builtAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps": ["check", "test", "build"],
    }
    manifest_path = artifacts_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("制品:", target.name)
    print("摘要:", manifest["sha256"])
    print("清单:", manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
script_path = out / "local_pipeline.py"
script_path.write_text(script_text, encoding="utf-8")
print("已写入:", script_path.name)
print("行数:", len(script_text.splitlines()))


proc = subprocess.run(
    [
        sys.executable,
        str(out / "local_pipeline.py"),
        "--project",
        str(project),
        "--output",
        str(out),
    ],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
print(proc.stdout.strip())
if proc.stderr.strip():
    print(proc.stderr.strip())
print("脚本退出码:", proc.returncode)


manifest_path = out / "artifacts" / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
artifact = out / "artifacts" / manifest["artifact"]
digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

print("制品清单:")
for key in ["project", "artifact", "size", "sha256", "builtAt", "steps"]:
    print(f"  {key:<9} {manifest[key]}")
print("摘要核对:", "一致" if digest == manifest["sha256"] else "不一致")

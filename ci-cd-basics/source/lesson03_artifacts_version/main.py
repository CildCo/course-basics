import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

project = data_path("pipeline-demo")

with tempfile.TemporaryDirectory(prefix="cicd-artifact-") as tmp:
    work = Path(tmp) / "pipeline-demo"
    shutil.copytree(project, work)
    subprocess.run(
        [
            sys.executable, "-m", "pip", "wheel", ".",
            "--no-deps", "--no-build-isolation", "--no-index",
            "--no-cache-dir", "-w", "dist",
        ],
        cwd=work,
        check=True,
        capture_output=True,
        text=True,
    )

    wheel = next((work / "dist").glob("*.whl"))
    print("制品名:", wheel.name)
    print("大小:", wheel.stat().st_size, "字节")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        for name in names:
            print("  ", name)
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")

print("\nMETADATA 前 8 行:")
print("\n".join(metadata.splitlines()[:8]))


import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(data_path("pipeline-demo") / "src"))

from pipeline_demo.release import artifact_name, bump, checksum, release_tag

current = "0.3.0"
print("当前版本:", current)
for part in ["patch", "minor", "major"]:
    print(f"  {part:<5} -> {bump(current, part)}")
print("发布标签:", release_tag("0.3.1", "a1b2c3d4e5"))
print("wheel 文件名:", artifact_name("Pipeline_Demo", "0.3.1"))
print("内容摘要:", checksum(b"pipeline-demo 0.3.1"))

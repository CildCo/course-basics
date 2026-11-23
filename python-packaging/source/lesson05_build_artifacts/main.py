import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

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


from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def build_wheel(project_dir, dist_dir):
    dist_dir = Path(dist_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="wordmeter-wheel-") as temp:
        work = Path(temp) / "project"
        shutil.copytree(project_dir, work)
        (work / "dist").mkdir()
        command = [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "-w",
            "dist",
        ]
        result = subprocess.run(
            command,
            cwd=work,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        print("$ python -m pip wheel . --no-deps --no-build-isolation -w dist")
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        print("\n".join(lines[-5:]))
        if result.returncode != 0:
            print(result.stderr)
            raise SystemExit(result.returncode)
        wheel = next((work / "dist").glob("*.whl"))
        target = dist_dir / wheel.name
        shutil.copy2(wheel, target)
    return target


if __name__ == "__main__":
    project = OUTPUT / "wordmeter_project"
    shutil.copytree(source, project)
    dist_dir = OUTPUT / "dist"
    wheel = build_wheel(project, dist_dir)
    print("wheel：", wheel.name, wheel.stat().st_size, "字节")


def build_sdist(project_dir, dist_dir):
    dist_dir = Path(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wordmeter-sdist-") as temp:
        work = Path(temp) / "project"
        shutil.copytree(project_dir, work)
        (work / "dist").mkdir()
        code = "from setuptools import build_meta; print(build_meta.build_sdist('dist'))"
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=work,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        print("$ python -c \"from setuptools import build_meta; print(build_meta.build_sdist('dist'))\"")
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        print("\n".join(lines[-3:]))
        if result.returncode != 0:
            print(result.stderr)
            raise SystemExit(result.returncode)
        sdist = next((work / "dist").glob("*.tar.gz"))
        target = dist_dir / sdist.name
        shutil.copy2(sdist, target)
    return target


if __name__ == "__main__":
    sdist = build_sdist(project, dist_dir)
    print("sdist：", sdist.name, sdist.stat().st_size, "字节")


import zipfile


if __name__ == "__main__":
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith("METADATA"))
        entry_name = next(name for name in names if name.endswith("entry_points.txt"))
        metadata = archive.read(metadata_name).decode("utf-8")
        entries = archive.read(entry_name).decode("utf-8")

    print(f"wheel 内 {len(names)} 个条目：")
    for name in names:
        print(" ", name)
    print()
    for line in metadata.splitlines():
        if line.startswith(("Name:", "Version:", "Requires-Python:", "License-Expression:")):
            print(line)
    print()
    print(entries.strip())


import tarfile


if __name__ == "__main__":
    with tarfile.open(sdist) as archive:
        names = archive.getnames()
    print(f"sdist 内 {len(names)} 个条目，前 12 个：")
    for name in names[:12]:
        print(" ", name)


import tarfile
import zipfile

import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


if __name__ == "__main__":
    with zipfile.ZipFile(wheel) as archive:
        wheel_count = len(archive.namelist())
    with tarfile.open(sdist) as archive:
        sdist_count = len(archive.getnames())

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    labels = ["wheel", "sdist"]
    sizes = [wheel.stat().st_size / 1024, sdist.stat().st_size / 1024]
    counts = [wheel_count, sdist_count]

    axes[0].bar(labels, sizes, color=["#5b8db8", "#8fbf9f"])
    axes[0].set_title("体积（KB）")
    axes[0].set_ylim(0, max(sizes) * 1.3)
    for index, value in enumerate(sizes):
        axes[0].text(index, value, f"{value:.1f}", ha="center", va="bottom", fontsize=9)

    axes[1].bar(labels, counts, color=["#5b8db8", "#8fbf9f"])
    axes[1].set_title("条目数")
    axes[1].set_ylim(0, max(counts) * 1.3)
    for index, value in enumerate(counts):
        axes[1].text(index, value, str(value), ha="center", va="bottom", fontsize=9)

    fig.suptitle("同一个项目的两种发布产物", fontsize=12)
    plt.tight_layout()


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

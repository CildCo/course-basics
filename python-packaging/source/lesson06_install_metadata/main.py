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
import zipfile


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
        result = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    wheel = build_wheel(project, OUTPUT / "dist")
    site = OUTPUT / "site-packages"
    site.mkdir()
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(site)

    print("site-packages 顶层：")
    for path in sorted(site.iterdir()):
        print(" ", path.name + ("/" if path.is_dir() else ""))
    print()
    dist_info = next(site.glob("*.dist-info"))
    print("dist-info 内容：")
    for path in sorted(dist_info.iterdir()):
        print(" ", path.name)


import importlib.metadata as md


if __name__ == "__main__":
    sys.path.insert(0, str(site))
    installed = md.distribution("wordmeter")
    print("名称：", installed.metadata["Name"])
    print("版本：", installed.version)
    print("Python 要求：", installed.metadata["Requires-Python"])
    print("可选依赖：", installed.metadata.get_all("Provides-Extra"))
    print("入口点：")
    for entry in installed.entry_points:
        print(" ", entry.group, entry.name, "->", entry.value)
    print("文件数：", len(list(installed.files or [])))
    sys.path.remove(str(site))


if __name__ == "__main__":
    sample = data_path("sample.txt")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(site)
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, "-m", "wordmeter", str(sample), "--json"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("$ python -m wordmeter sample.txt --json")
    print(result.stdout.strip())
    print("退出码：", result.returncode)


import importlib.metadata as md


if __name__ == "__main__":
    entry = next(item for item in installed.entry_points if item.name == "wordmeter")
    module_name, function_name = entry.value.split(":")
    code = f"from {module_name} import {function_name}\nraise SystemExit({function_name}())"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(site)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-c", code, str(sample)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("入口点：", entry.value)
    print(result.stdout.strip())
    print("退出码：", result.returncode)


if __name__ == "__main__":
    shutil.rmtree(site)
    print("安装目录还在：", site.exists())
    print("剩余发行版：", list(md.distributions(path=[str(site)])))


import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


def box(ax, x, y, width, height, label, color="#e8f1fb"):
    rect = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.04,rounding_size=0.08",
        linewidth=1,
        edgecolor="#4a6fa5",
        facecolor=color,
    )
    ax.add_patch(rect)
    ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=9)


if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    box(ax, 3.4, 4.1, 3.2, 0.55, "site-packages/", "#dbe9f7")
    box(ax, 0.6, 2.7, 3.0, 0.6, "wordmeter/", "#e6f4ea")
    box(ax, 3.7, 2.7, 3.4, 0.6, "wordmeter-0.1.0.dist-info/", "#fdf1dc")
    box(ax, 7.3, 2.7, 2.2, 0.6, "Scripts/", "#f2f0f7")

    for x, label in [(0.4, "__init__.py"), (1.6, "core.py"), (2.8, "cli.py")]:
        box(ax, x, 1.4, 1.1, 0.5, label, "#f7f7f2")
    for x, label in [(3.9, "METADATA"), (5.2, "RECORD"), (6.5, "entry_points")]:
        box(ax, x, 1.4, 1.2, 0.5, label, "#f7f7f2")
    box(ax, 7.6, 1.4, 1.6, 0.5, "wordmeter.exe", "#f7f7f2")

    for start, end in [
        ((5.0, 4.1), (2.1, 3.3)),
        ((5.0, 4.1), (5.4, 3.3)),
        ((5.0, 4.1), (8.4, 3.3)),
    ]:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="-", color="#9aa5b1", lw=0.8))

    ax.set_title("安装后的布局：包代码、元数据、入口脚本分开放", fontsize=12)
    plt.tight_layout()


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

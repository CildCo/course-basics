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


if __name__ == "__main__":
    project = OUTPUT / "wordmeter_project"
    shutil.copytree(source, project)
    for name in ["README.md", "LICENSE", "src/wordmeter/py.typed"]:
        path = project / name
        print(f"{name:24} 存在：{path.exists()}")

    readme = (project / "README.md").read_text(encoding="utf-8")
    print("README 行数：", len(readme.splitlines()))
    print("README 首行：", readme.splitlines()[0])


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
    wheel = build_wheel(project, OUTPUT / "dist")
    print("构建完成：", wheel.name)


import email


if __name__ == "__main__":
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith("METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
    message = email.message_from_string(metadata)

    print("关键元数据：")
    for key in [
        "Name",
        "Version",
        "Summary",
        "Requires-Python",
        "License-Expression",
        "Description-Content-Type",
        "Provides-Extra",
    ]:
        print(f"  {key}: {message.get(key)}")
    print("py.typed 在 wheel 中：", "wordmeter/py.typed" in names)
    print("LICENSE 在 wheel 中：", any(name.endswith("licenses/LICENSE") for name in names))
    print("入口点文件：", any(name.endswith("entry_points.txt") for name in names))


def check_release(wheel_path):
    with zipfile.ZipFile(wheel_path) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith("METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
    message = email.message_from_string(metadata)
    checks = [
        ("包名与预期一致", message["Name"] == "wordmeter"),
        ("版本号存在", bool(message["Version"])),
        ("Python 下限明确", message["Requires-Python"] == ">=3.9"),
        ("带类型标记", "wordmeter/py.typed" in names),
        ("许可证已记录", bool(message["License-Expression"])),
        ("README 进入元数据", message["Description-Content-Type"] == "text/markdown"),
        ("入口点存在", any(name.endswith("entry_points.txt") for name in names)),
    ]
    return checks


if __name__ == "__main__":
    checks = check_release(wheel)
    for name, passed in checks:
        print(("通过" if passed else "失败").ljust(4), name)
    print("全部通过：", all(passed for _, passed in checks))


import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


if __name__ == "__main__":
    rows = [[name, "通过" if passed else "失败"] for name, passed in checks]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=["检查项", "结果"],
        loc="center",
        cellLoc="left",
        colWidths=[0.62, 0.18],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.65)
    for row_index, (_, passed) in enumerate(checks, start=1):
        cell = table[row_index, 1]
        cell.set_facecolor("#e6f4ea" if passed else "#fbe3e3")
    for column in range(2):
        table[0, column].set_facecolor("#dbe9f7")
    ax.set_title("发布检查结果", fontsize=12, pad=18)
    plt.tight_layout()


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

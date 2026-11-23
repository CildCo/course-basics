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


import re


VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?$"
)


def parse(version):
    match = VERSION_RE.match(version)
    if not match:
        raise ValueError(f"不是合法版本：{version}")
    return match.groupdict()


def bump(version, part):
    data = parse(version)
    numbers = {key: int(data[key]) for key in ("major", "minor", "patch")}
    if part == "major":
        numbers = {"major": numbers["major"] + 1, "minor": 0, "patch": 0}
    elif part == "minor":
        numbers["minor"] += 1
        numbers["patch"] = 0
    elif part == "patch":
        numbers["patch"] += 1
    else:
        raise ValueError(part)
    return f"{numbers['major']}.{numbers['minor']}.{numbers['patch']}"


if __name__ == "__main__":
    for part in ["patch", "minor", "major"]:
        print(f"0.1.0 升 {part}：", bump("0.1.0", part))
    print("解析预发布：", parse("1.2.3-rc.1"))
    print("1.2 是否合法：", bool(VERSION_RE.match("1.2")))


def order_key(version):
    data = parse(version)
    numbers = tuple(int(data[key]) for key in ("major", "minor", "patch"))
    pre = data["pre"]
    if pre is None:
        return numbers + ((1,),)
    parts = []
    for piece in pre.split("."):
        parts.append((0, int(piece)) if piece.isdigit() else (1, piece))
    return numbers + ((0, tuple(parts)),)


if __name__ == "__main__":
    versions = ["1.0.0-beta.2", "1.0.0", "1.0.0-alpha.1", "1.0.0-rc.1", "1.0.0-beta.1"]
    print("按发布顺序：")
    for version in sorted(versions, key=order_key):
        print(" ", version)


if __name__ == "__main__":
    changes = [
        ("修复解析错误，不改变接口", "patch"),
        ("新增 --json 选项", "minor"),
        ("删除旧参数 --raw", "major"),
    ]
    for description, part in changes:
        print(f"{description} -> 升 {part} -> {bump('1.4.2', part)}")


import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


if __name__ == "__main__":
    versions = ["0.1.0", "0.1.1", "0.2.0", "1.0.0"]
    labels = ["首个版本", "修复问题", "新增功能", "破坏性变更"]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(range(len(versions)), [0] * len(versions), color="#7a9cc6", lw=3, zorder=1)
    ax.scatter(range(len(versions)), [0] * len(versions), s=160, color="#4a6fa5", zorder=2)
    for index, (version, label) in enumerate(zip(versions, labels)):
        offset = 0.35 if index % 2 == 0 else -0.45
        ax.annotate(
            f"{version}\n{label}",
            (index, 0),
            xytext=(index, offset),
            ha="center",
            va="center",
            fontsize=10,
            arrowprops=dict(arrowstyle="-", color="#9aa5b1", lw=0.8),
        )
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlim(-0.5, len(versions) - 0.5)
    ax.axis("off")
    ax.set_title("语义化版本：每次发布都说明变更级别", fontsize=12)
    plt.tight_layout()


import tomllib
from pathlib import Path
import shutil


if __name__ == "__main__":
    project = OUTPUT / "wordmeter_project"
    shutil.copytree(source, project)

    init = project / "src" / "wordmeter" / "__init__.py"
    init.write_text(
        init.read_text(encoding="utf-8").replace('__version__ = "0.1.0"', '__version__ = "0.2.0"'),
        encoding="utf-8",
    )

    pyproject = project / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace('version = "0.1.0"\n', 'dynamic = ["version"]\n')
    text += '\n[tool.setuptools.dynamic]\nversion = {attr = "wordmeter.__version__"}\n'
    pyproject.write_text(text, encoding="utf-8")

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    print("project.version：", data["project"].get("version"))
    print("project.dynamic：", data["project"].get("dynamic"))
    print("动态版本配置：", data["tool"]["setuptools"]["dynamic"])

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    result = subprocess.run(
        [sys.executable, "-c", "import wordmeter; print(wordmeter.__version__)"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("包内版本：", result.stdout.strip())


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

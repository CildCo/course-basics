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
import os
import shutil
import subprocess
import sys


if __name__ == "__main__":
    flat = OUTPUT / "flat_demo"
    flat.mkdir()
    shutil.copytree(source / "src" / "wordmeter", flat / "wordmeter")
    (flat / "demo.py").write_text(
        "from wordmeter.core import count_text\n\nprint(count_text('hello 世界'))\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-c", "import wordmeter; print(wordmeter.__file__)"],
        cwd=flat,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("扁平布局下导入到：", result.stdout.strip())
    print("退出码：", result.returncode)


from pathlib import Path
import os
import shutil
import subprocess
import sys


if __name__ == "__main__":
    project = OUTPUT / "wordmeter_project"
    shutil.copytree(source, project)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-c", "import wordmeter"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("不带 PYTHONPATH 时退出码：", result.returncode)
    print(result.stderr.strip().splitlines()[-1])

    env["PYTHONPATH"] = str(project / "src")
    result = subprocess.run(
        [sys.executable, "-c", "import wordmeter; print(wordmeter.__file__)"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("加入 src 后导入到：", result.stdout.strip())


from pathlib import Path


if __name__ == "__main__":
    files = sorted(
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    print(f"项目共 {len(files)} 个文件：")
    for item in files:
        print(" ", item)

    top_level = [path.name for path in (project / "src").iterdir() if path.is_dir()]
    print("src 下的顶层包：", top_level)


from pathlib import Path

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
    ax.text(x + width / 2, y + height / 2, label, ha="center", va="center", fontsize=10)


if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    box(ax, 3.5, 5.1, 3.0, 0.6, "wordmeter 项目", "#dbe9f7")
    box(ax, 0.3, 3.9, 2.3, 0.55, "pyproject.toml")
    box(ax, 2.9, 3.9, 1.9, 0.55, "src/", "#e6f4ea")
    box(ax, 5.2, 3.9, 1.9, 0.55, "tests/")
    box(ax, 7.4, 3.9, 2.3, 0.55, "README / LICENSE")
    box(ax, 2.9, 2.6, 2.2, 0.55, "wordmeter/", "#e6f4ea")
    for x, label in [(2.4, "__init__.py"), (3.7, "core.py"), (5.0, "cli.py")]:
        box(ax, x, 1.35, 1.2, 0.5, label, "#f7f7f2")
    for x, label in [(6.3, "__main__.py"), (7.6, "py.typed")]:
        box(ax, x, 1.35, 1.35, 0.5, label, "#f7f7f2")

    for start, end in [
        ((5.0, 5.1), (1.45, 4.45)),
        ((5.0, 5.1), (3.85, 4.45)),
        ((5.0, 5.1), (6.15, 4.45)),
        ((5.0, 5.1), (8.55, 4.45)),
        ((3.85, 3.9), (4.0, 3.15)),
        ((4.0, 2.6), (3.0, 1.85)),
        ((4.0, 2.6), (4.3, 1.85)),
        ((4.0, 2.6), (5.6, 1.85)),
        ((4.0, 2.6), (6.95, 1.85)),
        ((4.0, 2.6), (8.25, 1.85)),
    ]:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="-", color="#9aa5b1", lw=0.8))

    ax.set_title("src 布局：一个顶层包，配置和测试都在包外", fontsize=12)
    plt.tight_layout()


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

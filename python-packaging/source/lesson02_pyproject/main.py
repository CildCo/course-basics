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


from pathlib import Path
import shutil


if __name__ == "__main__":
    project = OUTPUT / "wordmeter_project"
    shutil.copytree(source, project)
    print((project / "pyproject.toml").read_text(encoding="utf-8"))


import tomllib


if __name__ == "__main__":
    text = (project / "pyproject.toml").read_text(encoding="utf-8")
    data = tomllib.loads(text)
    build = data["build-system"]
    meta = data["project"]

    print("构建后端：", build["build-backend"])
    print("构建依赖：", build["requires"])
    print("包名：", meta["name"])
    print("版本：", meta["version"])
    print("Python 下限：", meta["requires-python"])
    print("运行依赖：", meta["dependencies"])
    print("可选依赖：", meta["optional-dependencies"])
    print("入口点：", meta["scripts"])
    print("说明文档：", meta["readme"])
    print("许可证：", meta["license"])


import re
import sys


if __name__ == "__main__":
    name_rule = re.compile(r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$")
    for name in ["wordmeter", "word-meter", "WordMeter", "word meter"]:
        print(f"{name!r:14} -> {bool(name_rule.match(name))}")

    current = ".".join(map(str, sys.version_info[:3]))
    required = tuple(int(part) for part in meta["requires-python"].lstrip(">=").split("."))
    print("当前解释器：", current)
    print("满足 requires-python：", sys.version_info[:2] >= required)

    package_root = project / "src" / meta["name"]
    print("包目录存在：", package_root.is_dir())


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

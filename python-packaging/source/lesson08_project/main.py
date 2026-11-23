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
    release = OUTPUT / "release"
    release.mkdir()
    project = release / "wordmeter"
    shutil.copytree(source, project)

    init = project / "src" / "wordmeter" / "__init__.py"
    init.write_text(
        init.read_text(encoding="utf-8").replace('__version__ = "0.1.0"', '__version__ = "1.0.0"'),
        encoding="utf-8",
    )

    pyproject = project / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    text = text.replace('version = "0.1.0"\n', 'dynamic = ["version"]\n')
    text += '\n[tool.setuptools.dynamic]\nversion = {attr = "wordmeter.__version__"}\n'
    pyproject.write_text(text, encoding="utf-8")

    readme = project / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("wordmeter-0.1.0", "wordmeter-1.0.0"),
        encoding="utf-8",
    )

    (project / "MANIFEST.in").write_text(
        "include README.md\ninclude LICENSE\nrecursive-include tests *.py\n",
        encoding="utf-8",
    )

    files = sorted(
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    print(f"发布项目共 {len(files)} 个文件：")
    for item in files:
        print(" ", item)


if __name__ == "__main__":
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(result.stderr.strip())
    print("测试退出码：", result.returncode)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


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
        result = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("$ python -m pip wheel . --no-deps --no-build-isolation -w dist")
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        print("\n".join(lines[-4:]))
        if result.returncode != 0:
            print(result.stderr)
            raise SystemExit(result.returncode)
        wheel = next((work / "dist").glob("*.whl"))
        target = dist_dir / wheel.name
        shutil.copy2(wheel, target)
    return target


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
        print("\n".join(lines[-2:]))
        if result.returncode != 0:
            print(result.stderr)
            raise SystemExit(result.returncode)
        sdist = next((work / "dist").glob("*.tar.gz"))
        target = dist_dir / sdist.name
        shutil.copy2(sdist, target)
    return target


if __name__ == "__main__":
    dist_dir = release / "dist"
    wheel = build_wheel(project, dist_dir)
    sdist = build_sdist(project, dist_dir)
    print()
    print("wheel：", wheel.name, wheel.stat().st_size, "字节")
    print("sdist：", sdist.name, sdist.stat().st_size, "字节")


import zipfile


if __name__ == "__main__":
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith("METADATA"))
        entry_name = next(name for name in names if name.endswith("entry_points.txt"))
        metadata = archive.read(metadata_name).decode("utf-8")
        entries = archive.read(entry_name).decode("utf-8")

    print("包内文件：")
    for name in names:
        print(" ", name)
    print()
    for line in metadata.splitlines():
        if line.startswith(("Name:", "Version:", "Requires-Python:", "License-Expression:")):
            print(line)
    print()
    print(entries.strip())

    sample = data_path("sample.txt")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(wheel)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-m", "wordmeter", str(sample), "--json"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print()
    print("$ python -m wordmeter sample.txt --json")
    print(result.stdout.strip())
    print("退出码：", result.returncode)


if __name__ == "__main__":
    line = next(line for line in entries.splitlines() if "=" in line)
    command, target = line.split("=")
    module_name, function_name = target.strip().split(":")
    code = f"from {module_name} import {function_name}\nraise SystemExit({function_name}())"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(wheel)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-c", code, str(sample)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print("命令：", command.strip())
    print("入口：", target.strip())
    print(result.stdout.strip())
    print("退出码：", result.returncode)


import hashlib
import json


def digest(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


if __name__ == "__main__":
    manifest = {
        "name": "wordmeter",
        "version": "1.0.0",
        "requiresPython": ">=3.9",
        "entryPoint": "wordmeter = wordmeter.cli:main",
        "install": "python -m pip install wordmeter-1.0.0-py3-none-any.whl",
        "artifacts": [
            {
                "file": item.name,
                "bytes": item.stat().st_size,
                "sha256": digest(item),
            }
            for item in (wheel, sdist)
        ],
    }
    manifest_path = release / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(manifest_path.read_text(encoding="utf-8"))


from pathlib import Path
import shutil


if __name__ == "__main__":
    shutil.rmtree(OUTPUT, ignore_errors=True)
    print("运行产物已清理：", not OUTPUT.exists())

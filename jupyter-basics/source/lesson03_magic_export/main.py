import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

original_cwd = Path.cwd()

def find_assets():
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("没有找到 assets 目录")


assets = find_assets()
work = Path(tempfile.mkdtemp(prefix="jupyter-magic-"))
os.chdir(work)
print("assets 已找到：", assets.name == "assets")
print("临时目录已创建：", work.exists())


values = list(range(1000))


os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]


html_path = work / "demo.html"
command = [
    sys.executable,
    "-m",
    "jupyter",
    "nbconvert",
    "--to",
    "html",
    str(assets / "demo.ipynb"),
    "--output",
    str(html_path),
]
completed = subprocess.run(command, capture_output=True, text=True)
print("返回码：", completed.returncode)
print("HTML 已生成：", html_path.exists())
if html_path.exists():
    print("文件大小：", html_path.stat().st_size, "字节")


os.chdir(original_cwd)
shutil.rmtree(work)
print("已回到原目录：", Path.cwd().name)
print("临时目录已清理：", not work.exists())

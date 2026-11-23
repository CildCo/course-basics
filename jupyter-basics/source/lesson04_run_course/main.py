import asyncio
import sys
from pathlib import Path

import nbformat

# Windows 的默认事件循环不支持 zmq 需要的接口，切换成选择器循环
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def find_assets():
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("没有找到 assets 目录")


assets = find_assets()
course_dir = assets.parent
nb = nbformat.read(assets / "course-sample.ipynb", as_version=4)
spec = nb.metadata["kernelspec"]
print("内核名称：", spec["name"])
print("内核显示名：", spec["display_name"])
print("代码单元格数：", sum(1 for cell in nb.cells if cell.cell_type == "code"))
print("已保存的输出数：", sum(len(cell.get("outputs", [])) for cell in nb.cells))


from jupyter_client.kernelspec import KernelSpecManager

manager = KernelSpecManager()
available = sorted(manager.find_kernel_specs())
print("可用内核：", available)
print("python3 是否可用：", "python3" in available)
print("显示名称：", manager.get_kernel_spec("python3").display_name)


import logging

from nbclient import NotebookClient

# 演示用的内核名不存在，先把底层日志调安静，只看捕获结果
logging.getLogger("jupyter_client").setLevel(logging.CRITICAL)

try:
    NotebookClient(
        nb, timeout=30, kernel_name="missing-kernel-2026"
    ).execute()
except Exception as exc:
    print("捕获异常：", type(exc).__name__)
    print("含义：内核不存在或未注册")


import tempfile
from nbformat.v4 import new_code_cell, new_notebook

work = Path(tempfile.mkdtemp(prefix="jupyter-run-"))
missing_nb = new_notebook()
missing_nb.metadata["kernelspec"] = {
    "name": "python3",
    "display_name": "Python 3",
    "language": "python",
}
missing_nb.cells.append(new_code_cell("import package_that_does_not_exist_2026"))
result = NotebookClient(
    missing_nb,
    timeout=60,
    kernel_name="python3",
    resources={"metadata": {"path": str(work)}},
    allow_errors=True,
).execute()
error = next(
    output
    for cell in result.cells
    for output in cell.get("outputs", [])
    if output.output_type == "error"
)
print("错误类型：", error.ename)
print("错误信息：", error.evalue)


def run_in(folder):
    probe = new_notebook()
    probe.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    probe.cells.append(
        new_code_cell("from pathlib import Path\nprint('assets 可见：', Path('assets').is_dir())")
    )
    executed = NotebookClient(
        probe,
        timeout=60,
        kernel_name="python3",
        resources={"metadata": {"path": str(folder)}},
        allow_errors=False,
    ).execute()
    for cell in executed.cells:
        for output in cell.get("outputs", []):
            if output.output_type == "stream":
                return output.text.strip()
    return "没有输出"


print("在临时目录执行：", run_in(work))
print("在课程目录执行：", run_in(course_dir))


executed = NotebookClient(
    nb,
    timeout=60,
    kernel_name="python3",
    resources={"metadata": {"path": str(course_dir)}},
    allow_errors=False,
).execute()
for cell in executed.cells:
    if cell.cell_type != "code":
        continue
    for output in cell.get("outputs", []):
        if output.output_type == "stream":
            print(output.text.strip())


import shutil

shutil.rmtree(work)
print("临时目录已清理：", not work.exists())

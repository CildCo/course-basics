import asyncio
import sys
import tempfile
from pathlib import Path

# Windows 的默认事件循环不支持 zmq 需要的接口，切换成选择器循环
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

work = Path(tempfile.mkdtemp(prefix="jupyter-cells-"))
print("临时目录已创建：", work.exists())
print("目录名前缀：", work.name.startswith("jupyter-cells-"))


import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

nb = new_notebook()
nb.metadata["kernelspec"] = {
    "name": "python3",
    "display_name": "Python 3",
    "language": "python",
}
nb.cells.append(new_markdown_cell("## 新建的 Notebook\n\n这一格是说明文字。"))
nb.cells.append(new_code_cell("name = '示例课程'\nprint('你好，', name)"))
nb.cells.append(new_code_cell("print('1 + 1 =', 1 + 1)"))
nbformat.validate(nb)

notebook_path = work / "created.ipynb"
nbformat.write(nb, notebook_path)
print("单元格数：", len(nb.cells))
print("已保存：", notebook_path.name)
print("文件存在：", notebook_path.exists())


from nbclient import NotebookClient

client = NotebookClient(
    nb,
    timeout=60,
    kernel_name="python3",
    resources={"metadata": {"path": str(work)}},
    allow_errors=False,
)
executed = client.execute()
for cell in executed.cells:
    if cell.cell_type != "code":
        continue
    for output in cell.outputs:
        if output.output_type == "stream":
            print(f"第 {cell.execution_count} 个代码块：", output.text.strip())


from nbformat.v4 import new_code_cell

executed.cells.append(new_code_cell("print('追加的单元格')"))
nbformat.write(executed, work / "created.ipynb")
reloaded = nbformat.read(work / "created.ipynb", as_version=4)
print("保存后单元格数：", len(reloaded.cells))
print("最后一个单元格类型：", reloaded.cells[-1].cell_type)
print("执行计数：", [cell.execution_count for cell in reloaded.cells if cell.cell_type == "code"])


import shutil

shutil.rmtree(work)
print("临时目录已清理：", not work.exists())

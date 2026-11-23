import json
from pathlib import Path

def find_assets():
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("没有找到 assets 目录")


assets = find_assets()
path = assets / "demo.ipynb"
raw = json.loads(path.read_text(encoding="utf-8"))
print("顶层键：", sorted(raw.keys()))
print("nbformat：", raw["nbformat"], raw["nbformat_minor"])
print("文件大小：", path.stat().st_size, "字节")


for index, cell in enumerate(raw["cells"], 1):
    source = "".join(cell["source"]).strip().replace("\n", " ")
    print(index, cell["cell_type"], "|", source[:40])


spec = raw["metadata"]["kernelspec"]
info = raw["metadata"]["language_info"]
print("内核名称：", spec["name"])
print("内核显示名：", spec["display_name"])
print("语言：", spec["language"])
print("语言版本：", info["version"])


import nbformat

nb = nbformat.read(path, as_version=4)
nbformat.validate(nb)
print("nbformat 版本：", nb.nbformat, nb.nbformat_minor)
print("单元格数：", len(nb.cells))
print("第一个单元格：", nb.cells[0].cell_type)
print("结构校验：通过")


code_cells = [cell for cell in nb.cells if cell.cell_type == "code"]
with_output = [cell for cell in code_cells if cell.get("outputs")]
print("代码单元格：", len(code_cells))
print("带输出的单元格：", len(with_output))
print("markdown 单元格：", len(nb.cells) - len(code_cells))

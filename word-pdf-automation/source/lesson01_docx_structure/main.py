from pathlib import Path


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out_dir = Path.cwd() / "output"
out_dir.mkdir(exist_ok=True)

from docx import Document

document = Document(data_path("report-template.docx"))
print("段落数:", len(document.paragraphs))
print("表格数:", len(document.tables))


for index, paragraph in enumerate(document.paragraphs):
    print(index, f"[{paragraph.style.name}]", paragraph.text)


table = document.tables[0]
print("行数:", len(table.rows), "列数:", len(table.columns))
for row in table.rows:
    print([cell.text for cell in row.cells])


non_empty = [paragraph for paragraph in document.paragraphs if paragraph.text.strip()]
styles = sorted({paragraph.style.name for paragraph in document.paragraphs})
cell_count = sum(len(row.cells) for row in table.rows)

print("非空段落:", len(non_empty))
print("使用样式:", styles)
print("表格单元格:", cell_count)

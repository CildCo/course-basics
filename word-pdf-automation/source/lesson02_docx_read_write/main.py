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
paragraph_texts = [paragraph.text for paragraph in document.paragraphs]
print("段落列表:", paragraph_texts)

table_rows = [[cell.text for cell in row.cells] for row in document.tables[0].rows]
for row in table_rows:
    print(row)


new_document = Document()
new_document.add_heading("周报", level=1)
new_document.add_paragraph("本周完成了文档结构梳理和模板整理。")
new_document.add_paragraph("下周计划：批量生成月报并核对数据。")

table = new_document.add_table(rows=3, cols=2)
table.style = "Table Grid"
table.cell(0, 0).text = "任务"
table.cell(0, 1).text = "状态"
table.cell(1, 0).text = "模板整理"
table.cell(1, 1).text = "完成"
table.cell(2, 0).text = "批量生成"
table.cell(2, 1).text = "进行中"

target = out_dir / "new-document.docx"
new_document.save(target)
print("已保存:", target.name)


check = Document(target)
print("第一个段落:", check.paragraphs[0].text)
print("样式:", check.paragraphs[0].style.name)
print("段落数:", len(check.paragraphs), "表格数:", len(check.tables))

for row in check.tables[0].rows:
    print([cell.text for cell in row.cells])


paragraph = check.add_paragraph("补充：数据以系统导出为准。")
paragraph.runs[0].bold = True
check.save(target)

again = Document(target)
print("最后一段:", again.paragraphs[-1].text)
print("加粗:", again.paragraphs[-1].runs[0].bold)

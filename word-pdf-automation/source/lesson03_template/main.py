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

import re
from docx import Document

TEMPLATE = data_path("report-template.docx")
document = Document(TEMPLATE)

texts = [paragraph.text for paragraph in document.paragraphs]
texts += [
    cell.text
    for table in document.tables
    for row in table.rows
    for cell in row.cells
]
placeholders = sorted(set(re.findall(r"\{\{(\w+)\}\}", "\n".join(texts))))
print("发现占位符:", placeholders)


def fill_paragraphs(paragraphs, values):
    for paragraph in paragraphs:
        text = paragraph.text
        for key, value in values.items():
            text = text.replace("{{" + key + "}}", str(value))
        if text != paragraph.text:
            paragraph.text = text


def fill_document(document, values):
    fill_paragraphs(document.paragraphs, values)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                fill_paragraphs(cell.paragraphs, values)


REPORTS = [
    {"month": "2026-01", "owner": "王敏", "total": "186,400"},
    {"month": "2026-02", "owner": "李哲", "total": "172,800"},
    {"month": "2026-03", "owner": "周琳", "total": "203,500"},
]

for item in REPORTS:
    report = Document(TEMPLATE)
    fill_document(report, item)
    target = out_dir / f"report-{item['month']}.docx"
    report.save(target)
    print("已生成:", target.name)


check = Document(out_dir / "report-2026-01.docx")
print("段落:", [p.text for p in check.paragraphs if p.text.strip()])
print("合计行:", [cell.text for cell in check.tables[0].rows[3].cells])

remaining = sum("{{" in p.text for p in check.paragraphs)
remaining += sum(
    "{{" in cell.text
    for table in check.tables
    for row in table.rows
    for cell in row.cells
)
print("剩余占位符:", remaining)

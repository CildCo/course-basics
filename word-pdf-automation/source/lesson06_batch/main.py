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

import csv
import re

from docx import Document
from PyPDF2 import PdfReader, PdfWriter

CONTRACT_DIR = data_path("contracts")
files = sorted(CONTRACT_DIR.glob("*.docx"))
print("合同文件:", [file.name for file in files])


PATTERNS = {
    "contract_no": r"合同号：([A-Z0-9-]+)",
    "date": r"签署日期：(\d{4}-\d{2}-\d{2})",
    "amount": r"合同金额（元）：([\d.]+)",
}


def extract(path):
    text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    row = {"file": path.name}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, text)
        row[key] = match.group(1) if match else ""
    return row


rows = [extract(file) for file in files]
for row in rows:
    print(row)


summary_path = out_dir / "summary.csv"
fieldnames = ["contract_no", "date", "amount", "file"]
with summary_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(summary_path.read_text(encoding="utf-8"))


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

writer = PdfWriter()
for row in rows:
    part_path = out_dir / f"contract-{row['contract_no']}.pdf"
    canvas_obj = canvas.Canvas(str(part_path), pagesize=A4)
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.drawString(72, 760, f"Contract {row['contract_no']}")
    canvas_obj.setFont("Helvetica", 12)
    canvas_obj.drawString(72, 730, f"Date: {row['date']}")
    canvas_obj.drawString(72, 708, f"Amount (CNY): {row['amount']}")
    canvas_obj.drawString(72, 686, f"Source: {row['file']}")
    canvas_obj.save()
    writer.add_page(PdfReader(str(part_path)).pages[0])

merged_path = out_dir / "all-contracts.pdf"
with merged_path.open("wb") as file:
    writer.write(file)

print("单份 PDF:", len(rows), "份")
print("合并后页数:", len(PdfReader(str(merged_path)).pages))


with summary_path.open(encoding="utf-8") as file:
    check_rows = list(csv.DictReader(file))

total = sum(float(row["amount"]) for row in check_rows)
print("汇总行数:", len(check_rows))
print("合同总金额:", f"{total:,.2f}")
print("PDF 页数:", len(PdfReader(str(merged_path)).pages))

for name in ["summary.csv", "all-contracts.pdf"]:
    path = out_dir / name
    print(name, path.stat().st_size, "字节")

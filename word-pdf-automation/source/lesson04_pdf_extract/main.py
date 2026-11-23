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

import pdfplumber

SOURCE = data_path("sample.pdf")
with pdfplumber.open(SOURCE) as pdf:
    print("页数:", len(pdf.pages))
    for number, page in enumerate(pdf.pages, start=1):
        print(f"第{number}页尺寸:", round(page.width), "x", round(page.height))


with pdfplumber.open(SOURCE) as pdf:
    for number, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        lines = [line for line in text.splitlines() if line.strip()]
        print(f"第{number}页 字符数={len(text)} 行数={len(lines)}")
        print("  首行:", lines[0] if lines else "")


with pdfplumber.open(SOURCE) as pdf:
    for number, page in enumerate(pdf.pages, start=1):
        tables = page.extract_tables()
        print(f"第{number}页 表格数={len(tables)}")
        for table in tables:
            print("  表头:", table[0])
            print("  行数:", len(table) - 1)
            print("  第一行:", table[1])


with pdfplumber.open(SOURCE) as pdf:
    first_page = pdf.pages[0]
    table = first_page.extract_tables()[0]
    header = table[0]
    rows = [dict(zip(header, row)) for row in table[1:]]

print("字段:", header)
for row in rows:
    print(row)
print("金额合计:", sum(int(row["Amount"]) for row in rows))

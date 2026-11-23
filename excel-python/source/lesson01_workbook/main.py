from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

from openpyxl import load_workbook


book = load_workbook(data_path("sales.xlsx"), data_only=True)
print("工作表:", book.sheetnames)
sheet = book["sales"]
print("行数:", sheet.max_row, "列数:", sheet.max_column)
print("使用范围:", sheet.dimensions)


for coordinate in ["A1", "B2", "F2"]:
    cell = sheet[coordinate]
    print(f"{coordinate}: {cell.value!r}")

print("按行列号读取:", sheet.cell(row=2, column=3).value)


for row in sheet.iter_rows(min_row=1, max_row=3, values_only=True):
    print(row)


notes = book["说明"]
for row in notes.iter_rows(values_only=True):
    print(row)

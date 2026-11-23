from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import CellIsRule


sales = pd.read_excel(data_path("sales.xlsx"), sheet_name="sales")
sales["amount"] = (sales["units"] * sales["price"]).round(2)

book = Workbook()
sheet = book.active
sheet.title = "sales"
sheet.append(list(sales.columns))
for row in sales.itertuples(index=False):
    sheet.append(list(row))
print("写入行数:", sheet.max_row - 1)


header_fill = PatternFill("solid", fgColor="1F4E78")
for cell in sheet[1]:
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")

widths = {"A": 12, "B": 10, "C": 10, "D": 12, "E": 10, "F": 10, "G": 12}
for column, width in widths.items():
    sheet.column_dimensions[column].width = width


for row in sheet.iter_rows(min_row=2, min_col=6, max_col=7):
    for cell in row:
        cell.number_format = '#,##0.00'

sheet.conditional_formatting.add(
    f"G2:G{sheet.max_row}",
    CellIsRule(operator="greaterThan", formula=["1000"], fill=PatternFill("solid", fgColor="FFF2CC")),
)
print("条件格式区域:", [str(item.sqref) for item in sheet.conditional_formatting])


output = Path("output")
output.mkdir(exist_ok=True)
target = output / "styled-sales.xlsx"
book.save(target)
print("保存:", target, target.stat().st_size, "字节")

check = load_workbook(target)
check_sheet = check["sales"]
print("表头加粗:", check_sheet["A1"].font.bold)
print("表头填充:", check_sheet["A1"].fill.fgColor.rgb)
print("D 列宽:", check_sheet.column_dimensions["D"].width)
print("金额格式:", check_sheet["G2"].number_format)
print("条件格式:", [str(item.sqref) for item in check_sheet.conditional_formatting])


pd.read_excel(target).head(3)

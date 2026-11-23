from pathlib import Path

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Font, PatternFill


files = sorted(data_path("monthly").glob("sales-*.xlsx"))
frames = [pd.read_excel(path, sheet_name="sales") for path in files]
merged = pd.concat(frames, ignore_index=True)
merged["month"] = pd.to_datetime(merged["date"]).dt.to_period("M").astype("string")
merged["amount"] = (merged["units"] * merged["price"]).round(2)

monthly = merged.groupby("month").agg(
    orders=("date", "size"),
    units=("units", "sum"),
    amount=("amount", "sum"),
).reset_index()
monthly["环比"] = monthly["amount"].pct_change()
monthly["amount"] = monthly["amount"].round(2)
monthly


category = merged.pivot_table(
    index="category",
    columns="month",
    values="amount",
    aggfunc="sum",
    fill_value=0,
).round(2)
category["合计"] = category.sum(axis=1).round(2)
category


def build_report(target):
    detail = merged.sort_values("date")[["date", "region", "category", "product", "units", "price", "amount", "month"]]
    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        monthly.to_excel(writer, sheet_name="月度汇总", index=False)
        category.to_excel(writer, sheet_name="分类汇总", index=True)
        detail.to_excel(writer, sheet_name="明细", index=False)
    return target

output = Path("output")
output.mkdir(exist_ok=True)
target = output / "monthly-report.xlsx"
build_report(target)
print("保存:", target, target.stat().st_size, "字节")


book = load_workbook(target)
header_fill = PatternFill("solid", fgColor="1F4E78")
for name in ["月度汇总", "分类汇总", "明细"]:
    sheet = book[name]
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    sheet.freeze_panes = "A2"

summary_sheet = book["月度汇总"]
summary_sheet.column_dimensions["A"].width = 12
for column in ["B", "C", "D"]:
    summary_sheet.column_dimensions[column].width = 14
summary_sheet.column_dimensions["E"].width = 10

last_row = summary_sheet.max_row
total_row = last_row + 1
summary_sheet.cell(row=total_row, column=1, value="合计")
for column in ["B", "C", "D"]:
    summary_sheet[f"{column}{total_row}"] = f"=SUM({column}2:{column}{last_row})"
for cell in summary_sheet[total_row]:
    cell.font = Font(bold=True)

for row in summary_sheet.iter_rows(min_row=2, max_row=total_row, min_col=4, max_col=4):
    for cell in row:
        cell.number_format = '#,##0.00'
for row in summary_sheet.iter_rows(min_row=2, max_row=last_row, min_col=5, max_col=5):
    for cell in row:
        cell.number_format = '0.0%'

summary_sheet.conditional_formatting.add(
    f"D2:D{last_row}",
    DataBarRule(start_type="min", end_type="max", color="5B9BD5"),
)

chart = BarChart()
chart.title = "月度金额"
chart.y_axis.title = "金额"
chart.x_axis.title = "月份"
data = Reference(summary_sheet, min_col=4, min_row=1, max_row=last_row)
categories = Reference(summary_sheet, min_col=1, min_row=2, max_row=last_row)
chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)
summary_sheet.add_chart(chart, "G2")

book.calculation.fullCalcOnLoad = True
book.save(target)
print("样式、公式和图表已写入")


book = pd.read_excel(target, sheet_name=None)
print({name: frame.shape for name, frame in book.items()})
pd.read_excel(target, sheet_name="月度汇总")


check = load_workbook(target)
print("工作表:", check.sheetnames)
print("月度汇总冻结:", check["月度汇总"].freeze_panes)
print("图表数:", len(check["月度汇总"]._charts))
print("合计公式:", check["月度汇总"].cell(row=total_row, column=4).value)
print("条件格式:", [str(item.sqref) for item in check["月度汇总"].conditional_formatting])


print("月报完成")
print(f"- 覆盖月份: {', '.join(monthly['month'])}")
print(f"- 明细 {len(merged)} 行，总数量 {int(merged['units'].sum())}，总金额 {merged['amount'].sum():,.2f} 元。")
print(f"- 文件: {target}，大小 {target.stat().st_size} 字节。")

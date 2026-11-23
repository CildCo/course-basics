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
from openpyxl.chart import BarChart, Reference


sales = pd.read_excel(data_path("sales.xlsx"), sheet_name="sales")

book = Workbook()
detail = book.active
detail.title = "明细"
detail.append(["date", "region", "category", "product", "units", "price", "amount"])
for row in sales.itertuples(index=False):
    detail.append([row.date, row.region, row.category, row.product, int(row.units), float(row.price)])
for row_number in range(2, detail.max_row + 1):
    detail[f"G{row_number}"] = f"=E{row_number}*F{row_number}"
detail.freeze_panes = "A2"
print("明细行数:", detail.max_row - 1)


summary = book.create_sheet("汇总")
summary.append(["指标", "值"])
summary.append(["订单数", f"=COUNTA(明细!A2:A{detail.max_row})"])
summary.append(["总数量", f"=SUM(明细!E2:E{detail.max_row})"])
summary.append(["总金额", f"=SUM(明细!G2:G{detail.max_row})"])

category = sales.assign(amount=sales["units"] * sales["price"]).groupby("category")["amount"].sum().reset_index()
summary.append([])
summary.append(["分类", "金额"])
start_row = summary.max_row + 1
for row in category.itertuples(index=False):
    summary.append([row.category, round(float(row.amount), 2)])
print("分类汇总起始行:", start_row, "结束行:", summary.max_row)


chart = BarChart()
chart.title = "分类金额"
chart.y_axis.title = "金额"
chart.x_axis.title = "分类"
data = Reference(summary, min_col=2, min_row=start_row, max_row=summary.max_row)
categories = Reference(summary, min_col=1, min_row=start_row, max_row=summary.max_row)
chart.add_data(data, titles_from_data=False)
chart.set_categories(categories)
summary.add_chart(chart, "D2")
print("图表已添加")


output = Path("output")
output.mkdir(exist_ok=True)
target = output / "formula-chart.xlsx"
book.calculation.fullCalcOnLoad = True
book.save(target)
print("保存:", target, target.stat().st_size, "字节")

check = load_workbook(target)
print("冻结:", check["明细"].freeze_panes)
print("金额公式:", check["明细"]["G2"].value)
print("汇总公式:", check["汇总"]["B2"].value, check["汇总"]["B4"].value)
print("图表数:", len(check["汇总"]._charts))
print("Python 计算总金额:", round(float((sales["units"] * sales["price"]).sum()), 2))

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
sheet = book["sales"]
header = [cell.value for cell in sheet[1]]
print("表头:", header)
print("数据行:", sheet.max_row - 1)


rows = list(sheet.iter_rows(min_row=2, values_only=True))
print("第一行数据:", rows[0])
records = [dict(zip(header, row)) for row in rows]
print("记录数:", len(records))
records[0]


total_units = sum(int(record["units"]) for record in records)
total_amount = sum(int(record["units"]) * float(record["price"]) for record in records)
print("总数量:", total_units)
print("总金额:", round(total_amount, 2))


top = max(records, key=lambda record: int(record["units"]) * float(record["price"]))
print("最大金额商品:", top["product"], "数量:", top["units"], "单价:", top["price"])
print("金额:", round(int(top["units"]) * float(top["price"]), 2))


for row in sheet.iter_rows(min_row=2):
    if row[3].value == top["product"] and row[4].value == top["units"]:
        print("订单日期:", row[0].value.date())
        print("商品单元格:", row[3].coordinate, "数量单元格:", row[4].coordinate)
        break

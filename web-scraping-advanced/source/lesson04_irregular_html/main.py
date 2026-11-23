import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import re

import pandas as pd
from bs4 import BeautifulSoup

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"没有找到 assets/{name}")

SITE = data_path("site")
OUTPUT = SITE.parent.parent / "output"
OUTPUT.mkdir(exist_ok=True)
table_file = SITE / "table.html"
print("表格页面：", table_file.name)
print("文件存在：", table_file.exists())


tables = pd.read_html(table_file)
print("识别到的表格数：", len(tables))
raw = tables[0]
print("形状：", raw.shape)
print(raw.to_string(index=False))


soup = BeautifulSoup(table_file.read_text(encoding="utf-8"), "lxml")

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def parse_price(text):
    text = clean(text).replace(",", "")
    if not text or "待定" in text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None

rows = []
for tr in soup.select("#price-table tbody tr"):
    if "note" in (tr.get("class") or []):
        continue
    cells = tr.find_all("td")
    if not cells:
        continue
    first = cells[0]
    if first.get("colspan") == "2":
        course = clean(first.get_text(" "))
        instructor = ""
        rest = cells[1:]
    else:
        course = clean(first.get_text(" "))
        instructor = clean(cells[1].get_text(" "))
        rest = cells[2:]
    price_text = clean(rest[0].get_text(" "))
    rows.append(
        {
            "course": course,
            "instructor": instructor or None,
            "price_text": price_text,
            "price": parse_price(price_text),
            "lessons": int(re.sub(r"\D", "", rest[1].get_text())),
            "updated": clean(rest[2].get_text()),
        }
    )

table_df = pd.DataFrame(rows)
print(table_df.to_string(index=False))
print("缺讲师的课程：", table_df.loc[table_df["instructor"].isna(), "course"].tolist())
print("价格待定：", table_df.loc[table_df["price"].isna(), "course"].tolist())


cards = []
for card in soup.select("#irregular-cards article.mini-card"):
    title = clean(card.select_one("h3").get_text(" "))
    teacher_node = card.select_one(".teacher")
    price_node = card.select_one(".price")
    price_text = clean(price_node.get_text(" ")) if price_node else ""
    tags = [clean(tag.get_text(" ")) for tag in card.select(".tag")]
    cards.append(
        {
            "title": title,
            "teacher": clean(teacher_node.get_text(" ")) if teacher_node else None,
            "price_text": price_text or None,
            "price": parse_price(price_text),
            "tags": "、".join(tags) if tags else None,
        }
    )

card_df = pd.DataFrame(cards)
print(card_df.to_string(index=False))
print(
    "缺讲师：", card_df["teacher"].isna().sum(),
    "缺价格：", card_df["price"].isna().sum(),
    "缺标签：", card_df["tags"].isna().sum(),
)


table_out = OUTPUT / "price_table.csv"
cards_out = OUTPUT / "irregular_cards.csv"
table_df.to_csv(table_out, index=False, encoding="utf-8-sig")
card_df.to_csv(cards_out, index=False, encoding="utf-8-sig")
print("已写入：", table_out.name, "和", cards_out.name)
print("表格行数：", len(table_df), "卡片行数：", len(card_df))
print("价格均值（含待定为空）：", round(table_df["price"].mean(), 1))

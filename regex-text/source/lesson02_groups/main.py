import re

text = "2026-03-01 下单，2026-03-15 发货"
pattern = r"(\d{4})-(\d{2})-(\d{2})"

print("findall：", re.findall(pattern, text))
match = re.search(pattern, text)
print("整段：", match.group())
print("所有分组：", match.groups())
print("第 1 组：", match.group(1))
print("位置：", match.span())


pattern = r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
match = re.search(pattern, "2026-03-18")

print("字典：", match.groupdict())
print("按名字取：", match.group("month"))
print("命名分组仍然有编号：", match.group(1), match.group(2), match.group(3))


text = "价格 399 元或 金额 1200 元"
print("捕获标签：", re.findall(r"(价格|金额)\s*(\d+)", text))
print("不捕获标签：", re.findall(r"(?:价格|金额)\s*(\d+)", text))

print("重复单词：", re.findall(r"\b(\w+)\s+\1\b", "hello hello world world test"))

match = re.search(r"((\d{4})-(\d{2}))-(\d{2})", "2026-03-18")
print("嵌套分组：", match.groups())

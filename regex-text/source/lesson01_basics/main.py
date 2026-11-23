import re

text = "订单 A102 金额 399 元，订单 B7 金额 1200 元"
print("数字：", re.findall(r"\d+", text))
print("字母加数字的编号：", re.findall(r"[A-Z]\d+", text))
print("单词字符：", re.findall(r"\w+", text))
print("空白字符：", re.findall(r"\s+", text))


samples = ["a", "aa", "aaa", "aaaa"]
patterns = [r"a", r"a+", r"a{2}", r"a{2,3}", r"a{2,}"]

for pattern in patterns:
    matched = [s for s in samples if re.fullmatch(pattern, s)]
    print(f"{pattern:<8} 匹配 {matched}")


lines = ["ERROR 库存不足", "INFO 库存正常", "WARN 库存偏低"]
joined = "\n".join(lines)

print("match 只看开头：", [line for line in lines if re.match(r"ERROR", line)])
print("多行模式：", re.findall(r"^ERROR.*$", joined, re.MULTILINE))
print("单行模式：", re.findall(r"^ERROR.*$", joined))
print("完整日期：", bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", "2026-03-01")))
print("缺位日期：", bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", "2026-3-1")))
print("中途命中：", bool(re.search(r"\d{4}-\d{2}-\d{2}", "发货日期 2026-03-01 10:00")))

import re

log = """2026-03-01 09:12:33 INFO  user=alice action=login
2026-03-01 09:15:02 WARN  user=bob action=upload size=12MB
2026-03-01 09:18:44 ERROR user=alice action=download code=500"""

pattern = r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) (\w+)"
for match in re.finditer(pattern, log):
    print(match.group(1), match.group(2), match.group(3))

print("所有日期：", re.findall(r"\d{4}-\d{2}-\d{2}", log))


error = re.search(r"ERROR.*code=(\d+)", log)
print("错误码：", error.group(1) if error else "没有错误")

replaced = re.sub(r"\bERROR\b", "FAIL", log)
print(replaced.splitlines()[2])

print(re.split(r"\s+", "python   stdlib  re", maxsplit=2))


word = re.compile(r"\bpython\b", re.IGNORECASE)
text = "Python 的标准库很实用，python 脚本也容易读。"
print("匹配数量：", len(word.findall(text)))
print("替换：", word.sub("PYTHON", text))


import textwrap

paragraph = (
    "Python 标准库覆盖了日常脚本的大多数需求。"
    "先把常用模块串起来，遇到问题时再查文档，比背 API 更有效。"
)
print(textwrap.fill(paragraph, width=24))
print("---")
english = "Python is a readable language with a large standard library"
print(textwrap.shorten(english, width=30, placeholder="..."))
print("---")
print(textwrap.indent("- 第一条\n- 第二条", prefix="  "))

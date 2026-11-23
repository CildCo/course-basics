import re

text = "order=10086 status=paid"
print("search：", re.search(r"status=\w+", text))
print("match：", re.match(r"status=\w+", text))
print("match 从开头：", re.match(r"order=\w+", text))
print("fullmatch：", re.fullmatch(r"order=\d+ status=\w+", text))

match = re.search(r"status=(?P<status>\w+)", text)
print("分组和位置：", match.group("status"), match.span())


text = "u1001 42ms, u1002 108ms, u1003 7ms"
print("findall 有分组：", re.findall(r"(u\d+)\s+(\d+)ms", text))

for match in re.finditer(r"(?P<user>u\d+)\s+(?P<ms>\d+)ms", text):
    print(
        "finditer：",
        match.group("user"),
        int(match.group("ms")),
        "位置",
        match.span(),
    )


print("替换手机号：", re.sub(r"\d{3}-\d{4}-\d{4}", "***", "联系 138-1234-5678 或 139-0000-1111"))
print("只替换第一处：", re.sub(r"\d+", lambda m: str(int(m.group()) + 1), "第1章 共3节", count=1))
print("按分隔符切分：", re.split(r"[,;]\s*", "苹果, 香蕉; 橙子"))
print("保留分隔符：", re.split(r"(\d+)", "a1b22c"))

pattern = re.compile(r"error", re.IGNORECASE)
print("编译后复用：", pattern.findall("Error error ERROR"))

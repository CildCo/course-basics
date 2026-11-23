name = "小居"
days = 12
print(f"{name} 的 Python 课已经更新到 {days} 节")


raw = "  苹果, 香蕉, 橙子  "
items = raw.strip().split(",")
cleaned = [item.strip() for item in items]
print(cleaned)
print(" / ".join(cleaned))


text = "https://example.com/course"
print(text.replace("https://", ""))
print(text.startswith("https://"))
print(text.find("course"))


code = "PYTHON-2026"
print(code[:6])
print(code[-4:])
print(code.count("T"))

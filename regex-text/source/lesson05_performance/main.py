import re

html = "<b>加粗</b> 和 <b>斜体</b>"
print("贪婪：", re.findall(r"<b>.*</b>", html))
print("非贪婪：", re.findall(r"<b>.*?</b>", html))
print("否定字符类：", re.findall(r"<b>[^<]*</b>", html))


text = "aaaa"
for pattern in [r"a+", r"a+?", r"a{2,3}", r"a{2,3}?"]:
    print(f"{pattern:<8}", re.findall(pattern, text))


import time

text = "a" * 20 + "!"

start = time.perf_counter()
result = re.fullmatch(r"(a+)+b", text)
print("嵌套量词失败匹配：", result is None, f"{time.perf_counter() - start:.4f}s")

start = time.perf_counter()
result = re.fullmatch(r"a+b", text)
print("改写后失败匹配：", result is None, f"{time.perf_counter() - start:.6f}s")

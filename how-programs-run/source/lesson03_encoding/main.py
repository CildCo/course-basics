import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

text = "你好, Python"
encoded = text.encode("utf-8")

print("字符数：", len(text))
print("字节数：", len(encoded))
print("UTF-8 字节：", encoded.hex())
print("解码回来：", encoded.decode("utf-8"))


for char in ["A", "你", "🐍"]:
    data = char.encode("utf-8")
    print(f"{char} -> 字符数 {len(char)}，字节数 {len(data)}，{data.hex()}")


wrong = encoded.decode("latin-1")
print("错误解码：", repr(wrong))
print("直接看：", wrong)
print("恢复：", wrong.encode("latin-1").decode("utf-8"))


bom_data = text.encode("utf-8-sig")
print("前三个字节：", bom_data[:3].hex())
print("按 utf-8 解码前两个字符：", repr(bom_data.decode("utf-8")[:2]))
print("按 utf-8-sig 解码前两个字符：", repr(bom_data.decode("utf-8-sig")[:2]))

import traceback

try:
    int("abc")
except ValueError as error:
    print("类型：", type(error).__name__)
    print("消息：", error)
    print("最后一行：", traceback.format_exc().strip().splitlines()[-1])


def parse(text):
    return int(text)

def load(text):
    return parse(text)

try:
    load("abc")
except ValueError as error:
    frames = traceback.extract_tb(error.__traceback__)
    print("调用顺序：", [frame.name for frame in frames])


def parse(text):
    return int(text)

print(parse("18"))
try:
    parse("abc")
except ValueError:
    print("复现成功：parse('abc') 会抛 ValueError")

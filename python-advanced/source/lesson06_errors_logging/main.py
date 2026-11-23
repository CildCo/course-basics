class InsufficientBalance(Exception):
    pass

def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientBalance(f"余额不足：{balance} < {amount}")
    return balance - amount

try:
    withdraw(100, 300)
except InsufficientBalance as error:
    print("失败：", error)


def parse_age(text):
    try:
        return int(text)
    except ValueError as error:
        raise ValueError(f"年龄必须是数字：{text}") from error

try:
    parse_age("abc")
except ValueError as error:
    print("错误：", error)
    print("原因：", type(error.__cause__).__name__)


import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("demo")

logger.info("开始处理")
logger.warning("数据里有空值")
logger.error("这一条会失败")


def average(numbers):
    assert numbers, "列表不能为空"
    return sum(numbers) / len(numbers)

print(average([1, 2, 3]))
try:
    average([])
except AssertionError as error:
    print("断言失败：", error)

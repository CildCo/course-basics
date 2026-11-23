import logging
import sys

logger = logging.getLogger("demo")
logger.handlers.clear()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("开始处理")
logger.warning("有一条空数据")
logger.error("这一条会失败")


logger.setLevel(logging.WARNING)
logger.info("这条不会显示")
logger.warning("这条会显示")


def average(numbers):
    assert numbers, "列表不能为空"
    return sum(numbers) / len(numbers)

print(average([1, 2, 3]))
try:
    average([])
except AssertionError as error:
    print("断言失败：", error)

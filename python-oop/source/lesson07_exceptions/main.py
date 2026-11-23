class AppError(Exception):
    """所有业务异常的基类。"""


class ValidationError(AppError):
    """输入不合法。"""


class InventoryError(AppError):
    """库存相关错误。"""


class InsufficientStockError(InventoryError):
    def __init__(self, sku, requested, available):
        super().__init__(f"{sku} 库存不足：需要 {requested}，只剩 {available}")
        self.sku = sku
        self.requested = requested
        self.available = available


class NotFoundError(AppError):
    """对象不存在。"""


print(InsufficientStockError("KB-01", 9, 2))
print("继承链：", [cls.__name__ for cls in InsufficientStockError.__mro__[:4]])


def reserve(sku, qty, stock):
    if sku not in stock:
        raise NotFoundError(f"没有商品 {sku}")
    if qty > stock[sku]:
        raise InsufficientStockError(sku, qty, stock[sku])
    stock[sku] -= qty
    return stock[sku]


stock = {"KB-01": 5}
for sku, qty in [("KB-01", 3), ("KB-01", 9), ("MS-02", 1)]:
    try:
        print(sku, qty, "件 → 剩余", reserve(sku, qty, stock))
    except InsufficientStockError as exc:
        print("库存不足：", exc, "| 可用", exc.available)
    except NotFoundError as exc:
        print("找不到：", exc)


def handle_specific_first(exc):
    try:
        raise exc
    except InsufficientStockError:
        return "先处理具体的库存不足"
    except InventoryError:
        return "再处理库存大类"
    except AppError:
        return "最后兜底业务异常"


def handle_broad_first(exc):
    try:
        raise exc
    except AppError:
        return "宽泛分支先命中"
    except InsufficientStockError:
        return "永远不会执行到这里"


print(handle_specific_first(InsufficientStockError("KB-01", 9, 2)))
print(handle_specific_first(ValidationError("数量不合法")))
print(handle_broad_first(InsufficientStockError("KB-01", 9, 2)))


def load_timeout(raw):
    try:
        return int(raw)
    except ValueError as exc:
        raise ValidationError(f"超时配置不是整数：{raw!r}") from exc


try:
    load_timeout("abc")
except ValidationError as exc:
    print("捕获：", exc)
    print("原始原因：", type(exc.__cause__).__name__, "|", exc.__cause__)

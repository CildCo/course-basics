from abc import ABC, abstractmethod
from dataclasses import dataclass


class OutOfStockError(Exception):
    def __init__(self, sku, requested, available):
        super().__init__(f"{sku} 库存不足：需要 {requested}，可用 {available}")
        self.sku = sku
        self.requested = requested
        self.available = available


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    price: float

    def __post_init__(self):
        if self.price <= 0:
            raise ValueError("商品价格必须大于 0")


class Inventory:
    def __init__(self, products, stock):
        self.products = {product.sku: product for product in products}
        self.stock = dict(stock)

    def get(self, sku):
        if sku not in self.products:
            raise KeyError(f"没有商品 {sku}")
        return self.products[sku]

    def available(self, sku):
        return self.stock.get(sku, 0)

    def check(self, sku, qty):
        if qty <= 0:
            raise ValueError("数量必须大于 0")
        self.get(sku)
        available = self.available(sku)
        if qty > available:
            raise OutOfStockError(sku, qty, available)
        return available

    def reserve(self, sku, qty):
        self.check(sku, qty)
        self.stock[sku] -= qty

    def release(self, sku, qty):
        self.stock[sku] = self.available(sku) + qty


@dataclass(frozen=True)
class OrderLine:
    product: Product
    qty: int

    @property
    def subtotal(self):
        return round(self.product.price * self.qty, 2)


class DiscountStrategy(ABC):
    @abstractmethod
    def discount(self, subtotal: float) -> float:
        ...


class NoDiscount(DiscountStrategy):
    def discount(self, subtotal):
        return 0.0


class PercentageDiscount(DiscountStrategy):
    def __init__(self, rate):
        if not 0 < rate < 1:
            raise ValueError("折扣率必须在 0 到 1 之间")
        self.rate = rate

    def discount(self, subtotal):
        return round(subtotal * self.rate, 2)


class ThresholdDiscount(DiscountStrategy):
    def __init__(self, threshold, amount):
        if threshold <= 0 or amount < 0:
            raise ValueError("门槛必须大于 0，减免不能为负")
        if amount >= threshold:
            raise ValueError("减免金额应当小于门槛")
        self.threshold = threshold
        self.amount = amount

    def discount(self, subtotal):
        return float(self.amount) if subtotal >= self.threshold else 0.0


class Order:
    def __init__(self, order_no, inventory, discount=None):
        self.order_no = order_no
        self.inventory = inventory
        self.discount_strategy = discount or NoDiscount()
        self.lines = []
        self.status = "draft"
        self.discount_amount = 0.0
        self.total = 0.0

    def add(self, sku, qty):
        product = self.inventory.get(sku)
        for index, line in enumerate(self.lines):
            if line.product.sku == sku:
                new_qty = line.qty + qty
                self.inventory.check(sku, new_qty)
                self.lines[index] = OrderLine(product, new_qty)
                return
        self.inventory.check(sku, qty)
        self.lines.append(OrderLine(product, qty))

    @property
    def subtotal(self):
        return round(sum(line.subtotal for line in self.lines), 2)

    def checkout(self):
        if self.status != "draft":
            raise ValueError(f"订单状态 {self.status} 不允许结算")
        if not self.lines:
            raise ValueError("空订单不能结算")
        reserved = []
        try:
            for line in self.lines:
                self.inventory.reserve(line.product.sku, line.qty)
                reserved.append(line)
        except OutOfStockError:
            for line in reserved:
                self.inventory.release(line.product.sku, line.qty)
            raise
        self.discount_amount = self.discount_strategy.discount(self.subtotal)
        self.total = round(self.subtotal - self.discount_amount, 2)
        self.status = "settled"
        return self.total

    def cancel(self):
        if self.status != "settled":
            raise ValueError("只有已结算订单可以取消")
        for line in self.lines:
            self.inventory.release(line.product.sku, line.qty)
        self.status = "cancelled"

    def summary(self):
        rows = [f"订单 {self.order_no}（{self.status}）"]
        for line in self.lines:
            rows.append(
                f"  {line.product.name} x{line.qty} = {line.subtotal:.2f}"
            )
        rows.append(
            f"  小计 {self.subtotal:.2f}，优惠 {self.discount_amount:.2f}，"
            f"应付 {self.total:.2f}"
        )
        return "\n".join(rows)


products = [
    Product("KB-01", "机械键盘", 299.0),
    Product("MS-02", "无线鼠标", 89.0),
    Product("MN-27", "27 寸显示器", 1299.0),
]
inventory = Inventory(products, {"KB-01": 5, "MS-02": 3, "MN-27": 1})

order1 = Order("SO-1001", inventory, PercentageDiscount(0.1))
order1.add("KB-01", 2)
order1.add("MS-02", 2)
print(order1.summary())
print("第一单应付：", order1.checkout())
print(order1.summary())
print("结算后库存：", inventory.stock)


order2 = Order("SO-1002", inventory, ThresholdDiscount(1000, 100))

try:
    order2.add("MN-27", 2)
except OutOfStockError as exc:
    print("下单被拦截：", exc)

order2.add("MN-27", 1)
order2.add("KB-01", 1)

try:
    order2.add("MS-02", 0)
except ValueError as exc:
    print("非法数量被拦截：", exc)

print("\n" + order2.summary())
print("第二单应付：", order2.checkout())
print(order2.summary())
print("最终库存：", inventory.stock)

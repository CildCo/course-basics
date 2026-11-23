from dataclasses import dataclass, field, replace, FrozenInstanceError


@dataclass
class OrderLine:
    sku: str
    unit_price: float
    qty: int = 1
    tags: list[str] = field(default_factory=list)

    def subtotal(self):
        return round(self.unit_price * self.qty, 2)


line = OrderLine("KB-01", 299.0, 2)
print(line)
print("小计", line.subtotal())
print("内容相等：", line == OrderLine("KB-01", 299.0, 2))
line.tags.append("促销")
print("标签", line.tags)


a = OrderLine("MS-02", 89.0)
b = OrderLine("MS-02", 89.0)
a.tags.append("加购")
print("a 的标签：", a.tags)
print("b 的标签：", b.tags)
print("默认工厂给每个实例独立列表：", a.tags is not b.tags)


try:
    @dataclass
    class BadLine:
        sku: str
        tags: list = []

except ValueError as exc:
    print("定义阶段就报错：", exc)


@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "CNY"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("金额不能为负")

    def with_discount(self, rate):
        return replace(self, amount=round(self.amount * (1 - rate), 2))


price = Money(199.0)
print(price)
print("可哈希：", hash(price) == hash(Money(199.0)))

try:
    price.amount = 299.0
except FrozenInstanceError as exc:
    print("不可修改：", exc)

sale = price.with_discount(0.2)
print("原对象：", price)
print("新对象：", sale)

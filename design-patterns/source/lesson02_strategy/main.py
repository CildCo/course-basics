from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Order:
    order_id: str
    customer: str
    amount: float

class DiscountStrategy(Protocol):
    name: str
    def apply(self, amount: float) -> float: ...

@dataclass(frozen=True)
class NoDiscount:
    name: str = "无折扣"
    def apply(self, amount: float) -> float:
        return round(amount, 2)

@dataclass(frozen=True)
class PercentageDiscount:
    rate: float
    name: str = "百分比折扣"
    def apply(self, amount: float) -> float:
        return round(amount * self.rate, 2)

@dataclass(frozen=True)
class ThresholdDiscount:
    threshold: float
    off: float
    name: str = "满减"
    def apply(self, amount: float) -> float:
        return round(amount - self.off, 2) if amount >= self.threshold else round(amount, 2)

@dataclass(frozen=True)
class TierDiscount:
    name: str = "VIP 阶梯"
    def apply(self, amount: float) -> float:
        if amount >= 2000:
            return round(amount * 0.85, 2)
        if amount >= 1000:
            return round(amount * 0.90, 2)
        return round(amount * 0.95, 2)

strategies = [NoDiscount(), PercentageDiscount(0.95), ThresholdDiscount(500, 80), TierDiscount()]
print("可用策略:", [item.name for item in strategies])
print("阶梯策略示例:", TierDiscount().apply(1200.0))


def checkout(order, strategy):
    payable = strategy.apply(order.amount)
    return {
        "订单": order.order_id,
        "策略": strategy.name,
        "原价": order.amount,
        "应付": payable,
        "优惠": round(order.amount - payable, 2),
    }

scenarios = [
    (Order("B001", "普通", 260.0), NoDiscount()),
    (Order("B002", "会员", 880.0), PercentageDiscount(0.95)),
    (Order("B003", "活动", 600.0), ThresholdDiscount(500, 80)),
    (Order("B004", "VIP", 1200.0), TierDiscount()),
]
for order, strategy in scenarios:
    row = checkout(order, strategy)
    print(
        f"{row['订单']} {row['策略']:<6} 原价 {row['原价']:>7.2f} "
        f"应付 {row['应付']:>7.2f} 优惠 {row['优惠']:>6.2f}"
    )


def naive_discount(customer_type, amount):
    if customer_type == "普通":
        return round(amount, 2)
    if customer_type == "会员":
        return round(amount * 0.95, 2)
    if customer_type == "VIP":
        return TierDiscount().apply(amount)
    raise ValueError(customer_type)

comparisons = [
    ("普通", 260.0, NoDiscount()),
    ("会员", 880.0, PercentageDiscount(0.95)),
    ("VIP", 1200.0, TierDiscount()),
    ("VIP", 600.0, TierDiscount()),
]
for customer_type, amount, strategy in comparisons:
    old = naive_discount(customer_type, amount)
    new = strategy.apply(amount)
    assert old == new, (customer_type, amount, old, new)
    print(f"{customer_type:<2} {amount:>7.2f} if/else={old:>7.2f} 策略={new:>7.2f}")
print("两种写法输出一致，策略版把规则移到了独立类里")


STRATEGY_BY_CODE = {
    "none": NoDiscount(),
    "member": PercentageDiscount(0.95),
    "promo": ThresholdDiscount(500, 80),
    "vip": TierDiscount(),
}

def choose_strategy(code):
    if code not in STRATEGY_BY_CODE:
        raise KeyError(f"未知策略: {code}")
    return STRATEGY_BY_CODE[code]

print("策略编码:", sorted(STRATEGY_BY_CODE))
print("promo 应付:", checkout(Order("B005", "活动", 600.0), choose_strategy("promo"))["应付"])

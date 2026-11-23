def checkout_old(items, coupon=None, member=False, channel="standard"):
    subtotal = 0
    for item in items:
        subtotal = subtotal + item["price"] * item["qty"]
    discount = 0
    if coupon:
        if coupon == "SAVE10":
            if subtotal >= 100:
                discount = 10
        elif coupon == "SAVE20":
            if subtotal >= 200:
                discount = 20
    amount = subtotal - discount
    if member:
        amount = amount * 0.95
    if channel == "pickup":
        shipping = 0
    elif channel == "express":
        if amount >= 199:
            shipping = 0
        else:
            shipping = 15
    else:
        if amount >= 199:
            shipping = 0
        else:
            shipping = 10
    total = round(amount + shipping, 2)
    if member:
        label = "会员"
    else:
        label = "普通"
    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": shipping,
        "total": total,
        "label": label,
    }


ITEMS = [
    {"name": "键盘", "price": 199.0, "qty": 1},
    {"name": "鼠标垫", "price": 29.0, "qty": 2},
]

if __name__ == "__main__":
    print(checkout_old(ITEMS, coupon="SAVE10", member=True))


from dataclasses import asdict, dataclass


class CheckoutError(ValueError):
    """结算参数不合法。"""


@dataclass(frozen=True)
class Coupon:
    code: str
    discount: float
    min_subtotal: float


@dataclass(frozen=True)
class Checkout:
    subtotal: float
    discount: float
    shipping: float
    total: float
    label: str


FREE_SHIPPING = 199
EXPRESS_FEE = 15
STANDARD_FEE = 10
MEMBER_RATE = 0.95

COUPONS = {
    "SAVE10": Coupon("SAVE10", 10, 100),
    "SAVE20": Coupon("SAVE20", 20, 200),
}
CHANNELS = {"pickup", "standard", "express"}


def subtotal_of(items):
    return sum(item["price"] * item["qty"] for item in items)


def coupon_discount(code, subtotal):
    if not code:
        return 0.0
    coupon = COUPONS.get(code)
    if coupon is None:
        raise CheckoutError(f"未知优惠码：{code}，可用：{', '.join(sorted(COUPONS))}")
    if subtotal < coupon.min_subtotal:
        return 0.0
    return coupon.discount


def shipping_fee(channel, amount):
    if channel == "pickup":
        return 0.0
    if amount >= FREE_SHIPPING:
        return 0.0
    return EXPRESS_FEE if channel == "express" else STANDARD_FEE


def checkout(items, coupon=None, member=False, channel="standard"):
    if not items:
        raise CheckoutError("订单至少需要一件商品")
    if channel not in CHANNELS:
        raise CheckoutError(f"未知配送方式：{channel}，可用：{', '.join(sorted(CHANNELS))}")
    subtotal = subtotal_of(items)
    discount = coupon_discount(coupon, subtotal)
    payable = subtotal - discount
    if member:
        payable *= MEMBER_RATE
    shipping = shipping_fee(channel, payable)
    total = round(payable + shipping, 2)
    return Checkout(
        subtotal=round(subtotal, 2),
        discount=round(discount, 2),
        shipping=shipping,
        total=total,
        label="会员" if member else "普通",
    )


if __name__ == "__main__":
    print(checkout(ITEMS, coupon="SAVE10", member=True))


CASES = {
    "普通订单": {"items": ITEMS},
    "满 100 用券": {"items": ITEMS, "coupon": "SAVE10"},
    "会员 + 快递": {"items": ITEMS, "coupon": "SAVE10", "member": True, "channel": "express"},
    "自提": {"items": ITEMS, "channel": "pickup"},
    "低额用券": {
        "items": [{"name": "铅笔", "price": 5.0, "qty": 2}],
        "coupon": "SAVE20",
    },
}

if __name__ == "__main__":
    print(f"{'场景':<10} {'旧总价':>7} {'新总价':>7} 一致")
    for name, kwargs in CASES.items():
        old = checkout_old(**kwargs)
        new = asdict(checkout(**kwargs))
        print(f"{name:<10} {old['total']:>7.2f} {new['total']:>7.2f} {old == new}")


if __name__ == "__main__":
    error_cases = [
        ("未知优惠码", {"items": ITEMS, "coupon": "SAVE99"}),
        ("未知配送", {"items": ITEMS, "channel": "drone"}),
        ("空订单", {"items": []}),
    ]
    for name, kwargs in error_cases:
        try:
            checkout(**kwargs)
        except CheckoutError as exc:
            print(f"{name} -> {exc}")


CHECKLIST = [
    ("命名", "变量和函数名能读出业务含义"),
    ("单一职责", "每个函数只做一件事"),
    ("早返回", "异常路径先退出，主流程不嵌套"),
    ("纯函数", "计算不修改传入参数"),
    ("数据结构", "关键结果用数据类而不是裸字典"),
    ("错误信息", "异常包含字段名、非法值和可选值"),
    ("验证", "重构前后用同一批用例比较输出"),
]

if __name__ == "__main__":
    for index, (name, description) in enumerate(CHECKLIST, 1):
        print(f"{index}. [x] {name}：{description}")

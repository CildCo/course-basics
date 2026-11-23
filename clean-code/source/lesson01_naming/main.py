TAX_RATE = 0.08
MEMBER_RATE = 0.9

ORDERS = [
    {
        "id": "A1",
        "items": [
            {"name": "键盘", "price": 199.0, "qty": 1},
            {"name": "鼠标垫", "price": 29.0, "qty": 2},
        ],
    },
    {
        "id": "A2",
        "items": [{"name": "显示器", "price": 899.0, "qty": 1}],
    },
]


def calc(os_, t, m):
    s = 0
    for o in os_:
        x = 0
        for i in o["items"]:
            x += i["price"] * i["qty"]
        if m:
            x = x * MEMBER_RATE
        s += x
    s = s * (1 + t)
    return round(s, 2)


if __name__ == "__main__":
    print("旧实现总价：", calc(ORDERS, TAX_RATE, True))


def line_total(item):
    return item["price"] * item["qty"]


def order_subtotal(order):
    return sum(line_total(item) for item in order["items"])


def apply_member_discount(amount, is_member):
    if not is_member:
        return amount
    return amount * MEMBER_RATE


def with_tax(amount, tax_rate=TAX_RATE):
    return amount * (1 + tax_rate)


def calculate_total(orders, *, tax_rate=TAX_RATE, is_member=False):
    subtotal = sum(order_subtotal(order) for order in orders)
    discounted = apply_member_discount(subtotal, is_member)
    return round(with_tax(discounted, tax_rate), 2)


if __name__ == "__main__":
    new_total = calculate_total(ORDERS, is_member=True)
    old_total = calc(ORDERS, TAX_RATE, True)
    print("新实现总价：", new_total)
    print("旧实现总价：", old_total)
    print("结果一致：", new_total == old_total)


def shipping_label_old(amount, member):
    if amount > 0:
        if amount >= 99:
            return "包邮"
        else:
            if member:
                return "会员 5 元"
            else:
                return "10 元"
    else:
        return "无订单"


def shipping_label(amount, member):
    if amount <= 0:
        return "无订单"
    if amount >= 99:
        return "包邮"
    if member:
        return "会员 5 元"
    return "10 元"


if __name__ == "__main__":
    cases = [(0, False), (50, False), (50, True), (120, False)]
    for amount, member in cases:
        old = shipping_label_old(amount, member)
        new = shipping_label(amount, member)
        print(f"金额 {amount:>3} 会员 {member!s:<5} 旧：{old:<6} 新：{new:<6} 一致：{old == new}")

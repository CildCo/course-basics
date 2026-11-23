def add_item_old(item, cart=[]):
    cart.append(item)
    return cart


if __name__ == "__main__":
    first = add_item_old("键盘")
    second = add_item_old("鼠标")
    print("第一次调用后：", first)
    print("第二次调用后：", second)
    print("两次拿到同一个列表：", first is second)


def rank_old(orders):
    orders.sort(key=lambda order: order["total"], reverse=True)
    return orders


ORIGINAL = [
    {"id": "A1", "total": 120.0},
    {"id": "A2", "total": 340.0},
    {"id": "A3", "total": 80.0},
]

if __name__ == "__main__":
    ranked = rank_old(ORIGINAL)
    print("排序结果：", [order["id"] for order in ranked])
    print("原列表被改动：", [order["id"] for order in ORIGINAL])


def add_item(cart, item):
    return [*cart, item]


def rank_orders(orders):
    return sorted(orders, key=lambda order: order["total"], reverse=True)


if __name__ == "__main__":
    cart = []
    cart = add_item(cart, "键盘")
    cart = add_item(cart, "鼠标")
    print("新实现：", cart)
    print("默认参数不再共享：", add_item([], "铅笔") == ["铅笔"])

    original = [
        {"id": "A1", "total": 120.0},
        {"id": "A2", "total": 340.0},
        {"id": "A3", "total": 80.0},
    ]
    ranked = rank_orders(original)
    print("排序结果：", [order["id"] for order in ranked])
    print("原列表保持不变：", [order["id"] for order in original])


from dataclasses import dataclass


@dataclass(frozen=True)
class CartLine:
    name: str
    price: float
    qty: int = 1

    @property
    def total(self):
        return self.price * self.qty


if __name__ == "__main__":
    lines = [CartLine("键盘", 199.0), CartLine("鼠标", 59.0, 2)]
    print(lines)
    print("总价：", sum(line.total for line in lines))
    try:
        lines[0].qty = 3
    except Exception as exc:
        print("修改被拒绝：", type(exc).__name__)

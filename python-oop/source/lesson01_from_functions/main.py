cart = [
    {"name": "键盘", "price": 299.0, "qty": 1},
    {"name": "鼠标", "price": 89.0, "qty": 2},
]


def cart_total(items):
    return round(sum(item["price"] * item["qty"] for item in items), 2)


def apply_discount(items, rate):
    for item in items:
        item["price"] = round(item["price"] * (1 - rate), 2)


print("原价", cart_total(cart))
apply_discount(cart, 0.1)
print("九折后", cart_total(cart))
print("购物车数据", cart)


bad_item = {"name": "显示器", "price": 1299.0}
try:
    cart_total(cart + [bad_item])
except KeyError as exc:
    print("缺字段的条目把错误拖到了计算阶段：", exc)

cart[0]["qty"] = -3
print("负数数量也能算出总价：", cart_total(cart))


class CartItem:
    def __init__(self, name, price, qty=1):
        if price <= 0:
            raise ValueError("价格必须大于 0")
        if qty < 1:
            raise ValueError("数量至少为 1")
        self.name = name
        self.price = round(float(price), 2)
        self.qty = qty

    def subtotal(self):
        return round(self.price * self.qty, 2)


class ShoppingCart:
    def __init__(self):
        self.items = []

    def add(self, name, price, qty=1):
        self.items.append(CartItem(name, price, qty))

    def total(self):
        return round(sum(item.subtotal() for item in self.items), 2)

    def apply_discount(self, rate):
        if not 0 <= rate < 1:
            raise ValueError("折扣率必须在 0 到 1 之间")
        for item in self.items:
            item.price = round(item.price * (1 - rate), 2)


cart = ShoppingCart()
cart.add("键盘", 299.0)
cart.add("鼠标", 89.0, 2)
print("总价", cart.total())
cart.apply_discount(0.1)
print("九折后", cart.total())


try:
    cart.add("显示器", -10)
except ValueError as exc:
    print("非法数据在入口就被拦截：", exc)

print("购物车里的条目数：", len(cart.items))
print("第一件的单价：", cart.items[0].price)

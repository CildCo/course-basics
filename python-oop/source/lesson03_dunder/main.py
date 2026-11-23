class Money:
    def __init__(self, amount, currency="CNY"):
        self.amount = amount
        self.currency = currency


m1 = Money(19.9)
m2 = Money(19.9)
print(m1)
print("相等吗？", m1 == m2)


class Money:
    def __init__(self, amount, currency="CNY"):
        self.amount = round(float(amount), 2)
        self.currency = currency

    def __str__(self):
        return f"{self.amount:.2f} {self.currency}"

    def __repr__(self):
        return f"Money({self.amount!r}, {self.currency!r})"

    def __eq__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        return (self.amount, self.currency) == (other.amount, other.currency)

    def __hash__(self):
        return hash((self.amount, self.currency))

    def __add__(self, other):
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("不同币种不能直接相加")
        return Money(self.amount + other.amount, self.currency)


price = Money(19.9)
shipping = Money(6.0)
print("str：", str(price))
print("repr：", repr(price))
print("列表里的样子：", [price])
print("相等：", price == Money(19.9))
print("相加：", price + shipping)
print("set 去重：", {price, Money(19.9), shipping})


class Cart:
    def __init__(self, items=None):
        self.items = list(items or [])

    def __len__(self):
        return len(self.items)

    def __contains__(self, name):
        return name in self.items

    def __add__(self, other):
        return Cart(self.items + other.items)

    def __str__(self):
        return "购物车：" + "、".join(self.items)

    def __repr__(self):
        return f"Cart({self.items!r})"


a = Cart(["键盘"])
b = Cart(["鼠标", "显示器"])
print(a)
print(repr(a))
print("合并后：", a + b)
print("条目数：", len(a + b))
print("有鼠标吗：", "鼠标" in a + b)

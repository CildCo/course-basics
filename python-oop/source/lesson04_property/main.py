class Product:
    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock


product = Product("机械键盘", 299, 10)
product.price = -50
product.stock = -3
print(product.name, product.price, product.stock)


class Product:
    def __init__(self, name, price, stock):
        self.name = name
        self.price = price
        self.stock = stock

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("价格必须是数字")
        if value <= 0:
            raise ValueError("价格必须大于 0")
        self._price = round(float(value), 2)

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, value):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError("库存必须是整数")
        if value < 0:
            raise ValueError("库存不能为负")
        self._stock = value

    @property
    def total_value(self):
        return round(self._price * self._stock, 2)


product = Product("机械键盘", 299, 10)
print("价格", product.price)
print("库存", product.stock)
print("库存总值", product.total_value)


for field, value in [("price", -1), ("price", "299"), ("stock", -3), ("stock", 2.5)]:
    try:
        setattr(product, field, value)
    except ValueError as exc:
        print(f"{field}={value!r} 被拒绝：{exc}")

print("对象仍然保持合法状态：", product.price, product.stock)

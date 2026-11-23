ORDERS = [
    {"id": "A1", "name": "键盘", "qty": 1, "price": 199.0},
    {"id": "A2", "name": "鼠标", "qty": 2, "price": 59.0},
]


def invoice_text_old(orders):
    lines = ["发票"]
    for order in orders:
        lines.append(
            f"{order['id']} {order['name']} x{order['qty']} = "
            f"{order['price'] * order['qty']:.2f}"
        )
    total = 0
    for order in orders:
        total += order["price"] * order["qty"]
    lines.append(f"合计 {total:.2f}")
    return "\n".join(lines)


def receipt_text_old(orders):
    lines = ["小票"]
    for order in orders:
        lines.append(
            f"{order['id']} {order['name']} x{order['qty']} = "
            f"{order['price'] * order['qty']:.2f}"
        )
    total = 0
    for order in orders:
        total += order["price"] * order["qty"]
    lines.append(f"应付 {total:.2f}")
    return "\n".join(lines)


def email_text_old(orders):
    lines = ["您好，您的订单如下："]
    for order in orders:
        lines.append(
            f"{order['id']} {order['name']} x{order['qty']} = "
            f"{order['price'] * order['qty']:.2f}"
        )
    total = 0
    for order in orders:
        total += order["price"] * order["qty"]
    lines.append(f"共计 {total:.2f}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(invoice_text_old(ORDERS))
    print()
    print(receipt_text_old(ORDERS))
    print()
    print(email_text_old(ORDERS))


def order_line(order):
    amount = order["price"] * order["qty"]
    return f"{order['id']} {order['name']} x{order['qty']} = {amount:.2f}"


def order_total(orders):
    return sum(order["price"] * order["qty"] for order in orders)


def build_document(orders, title, footer):
    lines = [title]
    lines.extend(order_line(order) for order in orders)
    lines.append(f"{footer} {order_total(orders):.2f}")
    return "\n".join(lines)


def invoice_text(orders):
    return build_document(orders, "发票", "合计")


def receipt_text(orders):
    return build_document(orders, "小票", "应付")


def email_text(orders):
    return build_document(orders, "您好，您的订单如下：", "共计")


if __name__ == "__main__":
    pairs = [
        ("发票", invoice_text_old, invoice_text),
        ("小票", receipt_text_old, receipt_text),
        ("邮件", email_text_old, email_text),
    ]
    for name, old, new in pairs:
        print(f"{name}输出一致：", old(ORDERS) == new(ORDERS))


def build_v2(orders, kind="invoice", header=True, footer=True, upper=False, separator="\n"):
    title = {"invoice": "发票", "receipt": "小票"}.get(kind, kind)
    lines = []
    if header:
        lines.append(title)
    for order in orders:
        line = order_line(order)
        lines.append(line.upper() if upper else line)
    if footer:
        lines.append(f"{'TOTAL' if upper else '合计'} {order_total(orders):.2f}")
    return separator.join(lines)


if __name__ == "__main__":
    print(build_v2(ORDERS, kind="receipt", header=False))
    print()
    print("调用参数：kind / header / footer / upper / separator 五个开关")

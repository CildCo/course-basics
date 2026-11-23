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


def report_old(orders):
    lines = ["订单报表", "=" * 20]
    total = 0.0
    for order in orders:
        subtotal = 0.0
        for item in order["items"]:
            subtotal += item["price"] * item["qty"]
        total += subtotal
        lines.append(f"{order['id']}: {subtotal:.2f}")
    lines.append("-" * 20)
    lines.append(f"合计: {total:.2f}")
    lines.append(f"平均: {total / len(orders):.2f}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report_old(ORDERS))


from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    order_id: str
    subtotal: float


def order_subtotal(order):
    return sum(item["price"] * item["qty"] for item in order["items"])


def build_lines(orders):
    return [OrderLine(order["id"], order_subtotal(order)) for order in orders]


def summarize(lines):
    total = sum(line.subtotal for line in lines)
    average = total / len(lines) if lines else 0.0
    return total, average


def render_report(orders):
    lines = build_lines(orders)
    total, average = summarize(lines)
    body = [f"{line.order_id}: {line.subtotal:.2f}" for line in lines]
    return "\n".join(
        [
            "订单报表",
            "=" * 20,
            *body,
            "-" * 20,
            f"合计: {total:.2f}",
            f"平均: {average:.2f}",
        ]
    )


if __name__ == "__main__":
    print(render_report(ORDERS))


if __name__ == "__main__":
    old_text = report_old(ORDERS)
    new_text = render_report(ORDERS)
    print("输出完全相同：", old_text == new_text)
    print("字符数：", len(new_text))

    total, average = summarize(build_lines(ORDERS))
    print("单独测试汇总：", round(total, 2), round(average, 2))

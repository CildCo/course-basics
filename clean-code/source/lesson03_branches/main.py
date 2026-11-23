REFUND_WINDOW_DAYS = 7

ORDERS = [
    {"id": "A1", "paid": True, "delivered": True, "days_since_delivery": 3, "opened": False, "member": False},
    {"id": "A2", "paid": True, "delivered": True, "days_since_delivery": 3, "opened": True, "member": False},
    {"id": "A3", "paid": True, "delivered": True, "days_since_delivery": 3, "opened": True, "member": True},
    {"id": "A4", "paid": True, "delivered": True, "days_since_delivery": 10, "opened": False, "member": False},
    {"id": "A5", "paid": True, "delivered": False, "days_since_delivery": 0, "opened": False, "member": False},
    {"id": "A6", "paid": False, "delivered": False, "days_since_delivery": 0, "opened": False, "member": True},
]


def can_refund_old(order):
    if order["paid"]:
        if order["delivered"]:
            if order["days_since_delivery"] <= REFUND_WINDOW_DAYS:
                if not order["opened"] or order["member"]:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return True
    else:
        return False


if __name__ == "__main__":
    for order in ORDERS:
        print(order["id"], can_refund_old(order))


def can_refund(order):
    if not order["paid"]:
        return False
    if not order["delivered"]:
        return True
    if order["days_since_delivery"] > REFUND_WINDOW_DAYS:
        return False
    if order["opened"] and not order["member"]:
        return False
    return True


if __name__ == "__main__":
    for order in ORDERS:
        old = can_refund_old(order)
        new = can_refund(order)
        print(f"{order['id']} 旧：{old!s:<5} 新：{new!s:<5} 一致：{old == new}")


def refund_decision(order):
    is_paid = order["paid"]
    is_delivered = order["delivered"]
    within_window = order["days_since_delivery"] <= REFUND_WINDOW_DAYS
    opened_by_non_member = order["opened"] and not order["member"]

    if not is_paid:
        return False, "未支付"
    if not is_delivered:
        return True, "未发货，可直接取消"
    if not within_window:
        return False, f"超过 {REFUND_WINDOW_DAYS} 天"
    if opened_by_non_member:
        return False, "已拆封且不是会员"
    return True, "可以退款"


if __name__ == "__main__":
    for order in ORDERS:
        allowed, reason = refund_decision(order)
        print(f"{order['id']} {allowed!s:<5} {reason}")

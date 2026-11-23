def shipping_fee_old(channel, amount, member):
    if channel == "pickup":
        return 0
    elif channel == "standard":
        if amount >= 99:
            return 0
        elif member:
            return 5
        else:
            return 10
    elif channel == "express":
        if amount >= 199:
            return 0
        else:
            return 15
    else:
        raise ValueError(f"未知配送方式：{channel}")


CASES = [
    ("pickup", 50, False),
    ("standard", 50, False),
    ("standard", 50, True),
    ("standard", 120, False),
    ("express", 150, False),
    ("express", 250, True),
]

if __name__ == "__main__":
    for channel, amount, member in CASES:
        print(channel, amount, member, shipping_fee_old(channel, amount, member))


STANDARD_FREE = 99
EXPRESS_FREE = 199


def pickup_rule(amount, member):
    return 0


def standard_rule(amount, member):
    if amount >= STANDARD_FREE:
        return 0
    return 5 if member else 10


def express_rule(amount, member):
    if amount >= EXPRESS_FREE:
        return 0
    return 15


SHIPPING_RULES = {
    "pickup": pickup_rule,
    "standard": standard_rule,
    "express": express_rule,
}


def shipping_fee(channel, amount, member):
    try:
        rule = SHIPPING_RULES[channel]
    except KeyError as exc:
        raise ValueError(f"未知配送方式：{channel}") from exc
    return rule(amount, member)


if __name__ == "__main__":
    print("已注册规则：", sorted(SHIPPING_RULES))


if __name__ == "__main__":
    print(f"{'方式':<8} {'金额':>4} {'会员':<5} {'旧':>4} {'新':>4} 一致")
    for channel, amount, member in CASES:
        old = shipping_fee_old(channel, amount, member)
        new = shipping_fee(channel, amount, member)
        print(
            f"{channel:<8} {amount:>4} {member!s:<5} {old:>4} {new:>4} {old == new}"
        )

    try:
        shipping_fee("drone", 100, False)
    except ValueError as exc:
        print("未知方式：", exc, "| 起因：", type(exc.__cause__).__name__)

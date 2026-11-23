def discount_rate(customer_type, amount):
    if customer_type == "普通":
        return 1.0
    elif customer_type == "会员":
        return 0.95
    elif customer_type == "VIP":
        if amount >= 1000:
            return 0.85
        return 0.90
    elif customer_type == "员工":
        return 0.80
    else:
        raise ValueError(f"未知客户类型: {customer_type}")

orders = [
    ("A001", "普通", 260.0),
    ("A002", "会员", 880.0),
    ("A003", "VIP", 1200.0),
    ("A004", "VIP", 600.0),
    ("A005", "员工", 320.0),
]

for order_id, customer_type, amount in orders:
    rate = discount_rate(customer_type, amount)
    print(f"{order_id} {customer_type:<2} 原价 {amount:>7.2f} 折扣 {rate:.2f} 应付 {amount * rate:>7.2f}")


def discount_rate_v2(customer_type, amount, month):
    if customer_type == "普通":
        rate = 1.0
    elif customer_type == "会员":
        rate = 0.95
    elif customer_type == "VIP":
        rate = 0.85 if amount >= 1000 else 0.90
    elif customer_type == "员工":
        rate = 0.80
    elif customer_type == "企业":
        rate = 0.88 if amount >= 5000 else 0.92
    else:
        raise ValueError(f"未知客户类型: {customer_type}")

    if month in (6, 11):
        rate -= 0.03
    if customer_type == "VIP" and month == 8:
        rate -= 0.02
    return max(rate, 0.60)

before = discount_rate("VIP", 1200.0)
after = discount_rate_v2("VIP", 1200.0, month=11)
print("同一笔 VIP 订单")
print("旧规则折扣率:", before)
print("11 月新规则折扣率:", after)
print("新增规则后，旧调用方也需要跟着改参数")


problems = [
    ("新增规则要改旧函数", "每加一个客户类型或活动，都要编辑同一段分支"),
    ("判断顺序容易出错", "VIP 与活动折扣谁先谁后，会改变最终金额"),
    ("难以单独测试", "想测 11 月 VIP，必须先构造完整参数组合"),
    ("调用方被迫知道细节", "调用方要传 month，哪怕这次活动与它无关"),
]
for index, (problem, detail) in enumerate(problems, 1):
    print(f"{index}. {problem}：{detail}")
print("\n后面几节分别处理：选择变化、创建对象、适配接口、解耦通知和隔离存储。")


cases = [("普通", 260.0), ("会员", 880.0), ("VIP", 1200.0), ("企业", 6000.0), ("游客", 100.0)]
for customer_type, amount in cases:
    try:
        print(customer_type, amount, "->", discount_rate_v2(customer_type, amount, month=1))
    except ValueError as exc:
        print(customer_type, amount, "->", exc)

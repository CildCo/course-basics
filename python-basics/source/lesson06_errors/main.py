try:
    result = 10 / 0
except ZeroDivisionError:
    print("除数不能为 0")
else:
    print("结果：", result)


def safe_int(text):
    try:
        return int(text)
    except ValueError:
        return None

print(safe_int("18"))
print(safe_int("abc"))


try:
    value = int("7")
except ValueError:
    print("转换失败")
else:
    print("转换成功：", value)
finally:
    print("这一步总会执行")


def withdraw(balance, amount):
    if amount > balance:
        raise ValueError("余额不足")
    return balance - amount

try:
    print(withdraw(100, 30))
    print(withdraw(100, 300))
except ValueError as error:
    print("操作失败：", error)

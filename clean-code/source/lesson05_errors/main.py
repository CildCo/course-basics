def parse_amount_old(text):
    try:
        return float(text.replace("元", ""))
    except:
        return None


if __name__ == "__main__":
    print("合法值：", parse_amount_old("12.5元"))
    print("非法值：", parse_amount_old("abc"))
    print("负数：", parse_amount_old("-3"))
    values = ["10", "oops", "5"]
    print("静默忽略后合计：", sum(v for v in (parse_amount_old(v) for v in values) if v is not None))


class ValidationError(ValueError):
    """输入不符合业务规则。"""


def parse_amount(text):
    cleaned = text.strip().removesuffix("元")
    if not cleaned:
        raise ValidationError("金额不能为空")
    try:
        value = float(cleaned)
    except ValueError as exc:
        raise ValidationError(f"金额格式不正确：{text!r}，期望数字，例如 12.5 或 12.5元") from exc
    if value < 0:
        raise ValidationError(f"金额不能为负数：{value}")
    return value


if __name__ == "__main__":
    for text in ["10", "12.5元", " 8 "]:
        print(f"{text!r} -> {parse_amount(text)}")


if __name__ == "__main__":
    for text in ["", "abc", "-3"]:
        try:
            parse_amount(text)
        except ValidationError as exc:
            print(f"{text!r} -> {type(exc).__name__}: {exc}")
            if exc.__cause__ is not None:
                print("  起因：", type(exc.__cause__).__name__, exc.__cause__)


def read_total(values):
    return sum(parse_amount(value) for value in values)


if __name__ == "__main__":
    try:
        read_total(["10", "oops", "5"])
    except ValidationError as exc:
        print("整批失败：", exc)

    print("正常数据合计：", read_total(["10", "5", "2.5元"]))

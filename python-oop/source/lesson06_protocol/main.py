from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    def pay(self, amount: float) -> str:
        ...

    @abstractmethod
    def refund(self, order_no: str, amount: float) -> str:
        ...


class AlipayGateway(PaymentGateway):
    def pay(self, amount):
        return f"支付宝支付 {amount:.2f} 元"

    def refund(self, order_no, amount):
        return f"支付宝退款 {amount:.2f} 元（订单 {order_no}）"


class WechatGateway(PaymentGateway):
    def pay(self, amount):
        return f"微信支付 {amount:.2f} 元"

    def refund(self, order_no, amount):
        return f"微信退款 {amount:.2f} 元（订单 {order_no}）"


try:
    PaymentGateway()
except TypeError as exc:
    print("抽象基类不能直接实例化：", exc)

for gateway in [AlipayGateway(), WechatGateway()]:
    print(gateway.pay(99.0))


class BrokenGateway(PaymentGateway):
    def pay(self, amount):
        return f"只实现了付款 {amount}"


try:
    BrokenGateway()
except TypeError as exc:
    print("缺少 refund 也无法实例化：", exc)


from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    def send(self, message: str) -> str:
        ...


class EmailNotifier:
    def send(self, message):
        return f"邮件：{message}"


class SmsNotifier:
    def send(self, message):
        return f"短信：{message}"


def notify(notifier: Notifier, message: str) -> str:
    return notifier.send(message)


print(notify(EmailNotifier(), "订单已发货"))
print(notify(SmsNotifier(), "验证码 4821"))
print("EmailNotifier 符合 Notifier：", isinstance(EmailNotifier(), Notifier))


class Logger:
    def send(self, message):
        return f"日志：{message}"


print("没有继承也能传入：", notify(Logger(), "库存同步完成"))


class BrokenNotifier:
    def write(self, message):
        return message


print("方法名不匹配：", isinstance(BrokenNotifier(), Notifier))

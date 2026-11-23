from dataclasses import dataclass
from typing import Protocol

class PaymentGateway(Protocol):
    name: str
    def pay(self, amount: float) -> dict: ...

@dataclass
class AlipayGateway:
    name: str = "支付宝"
    def pay(self, amount: float) -> dict:
        return {"channel": self.name, "amount": amount, "status": "成功"}

@dataclass
class WeChatGateway:
    name: str = "微信支付"
    def pay(self, amount: float) -> dict:
        return {"channel": self.name, "amount": amount, "status": "成功"}

@dataclass
class CardGateway:
    name: str = "银行卡"
    def pay(self, amount: float) -> dict:
        return {"channel": self.name, "amount": amount, "status": "待银行确认"}

def create_payment_naive(channel):
    if channel == "alipay":
        return AlipayGateway()
    if channel == "wechat":
        return WeChatGateway()
    if channel == "card":
        return CardGateway()
    raise ValueError(f"未知渠道: {channel}")

print("初始渠道:", [create_payment_naive(name).name for name in ["alipay", "wechat", "card"]])


@dataclass
class BalanceGateway:
    name: str = "余额支付"
    def pay(self, amount: float) -> dict:
        return {"channel": self.name, "amount": amount, "status": "成功"}

def create_payment_naive_v2(channel):
    if channel == "alipay":
        return AlipayGateway()
    if channel == "wechat":
        return WeChatGateway()
    if channel == "card":
        return CardGateway()
    if channel == "balance":
        return BalanceGateway()
    raise ValueError(f"未知渠道: {channel}")

def checkout(channel, amount):
    gateway = create_payment_naive_v2(channel)
    return gateway.pay(amount)

print(checkout("balance", 128.0))
print("新增渠道时，工厂从 3 个分支变成 4 个，调用方依旧直接调用 checkout")


PAYMENT_REGISTRY = {}

def register_payment(name):
    def wrapper(cls):
        PAYMENT_REGISTRY[name] = cls
        return cls
    return wrapper

@register_payment("alipay")
class Alipay:
    def pay(self, amount):
        return {"channel": "支付宝", "amount": amount, "status": "成功"}

@register_payment("wechat")
class WeChat:
    def pay(self, amount):
        return {"channel": "微信支付", "amount": amount, "status": "成功"}

@register_payment("card")
class Card:
    def pay(self, amount):
        return {"channel": "银行卡", "amount": amount, "status": "待银行确认"}

def create_payment(name):
    if name not in PAYMENT_REGISTRY:
        raise ValueError(f"未知渠道: {name}")
    return PAYMENT_REGISTRY[name]()

def checkout_v2(channel, amount):
    return create_payment(channel).pay(amount)

print("注册表:", sorted(PAYMENT_REGISTRY))
for channel in ["alipay", "wechat", "card"]:
    print(checkout_v2(channel, 99.0))


@register_payment("balance")
class Balance:
    def pay(self, amount):
        return {"channel": "余额支付", "amount": amount, "status": "成功"}

print("新增后的注册表:", sorted(PAYMENT_REGISTRY))
print("同一个调用方:", checkout_v2("balance", 66.0))


NOTIFY_REGISTRY = {}

def register_notifier(name):
    def wrapper(factory):
        NOTIFY_REGISTRY[name] = factory
        return factory
    return wrapper

@register_notifier("sms")
def send_sms(message):
    return f"短信：{message}"

@register_notifier("email")
def send_email(message):
    return f"邮件：{message}"

def notify(channel, message):
    if channel not in NOTIFY_REGISTRY:
        raise ValueError(f"未知通知渠道: {channel}")
    return NOTIFY_REGISTRY[channel](message)

print(notify("sms", "订单已发货"))
print(notify("email", "订单已发货"))
print("通知注册表:", sorted(NOTIFY_REGISTRY))

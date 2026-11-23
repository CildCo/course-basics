from dataclasses import dataclass
from typing import Protocol

class Payment(Protocol):
    def pay(self, amount: float) -> dict: ...

@dataclass
class BasePayment:
    def pay(self, amount: float) -> dict:
        return {"amount": amount, "channel": "base", "status": "成功"}

@dataclass
class LoggedPayment:
    inner: Payment
    def pay(self, amount: float) -> dict:
        print(f"[日志] 开始支付 {amount:.2f}")
        result = self.inner.pay(amount)
        print(f"[日志] 支付结束，状态 {result['status']}")
        return result

payment = LoggedPayment(BasePayment())
print(payment.pay(100.0))
print("包装后仍然是 pay(amount) 接口")


import time
from functools import wraps

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[计时] {func.__name__} 用时 {elapsed:.2f} ms")
        return result
    return wrapper

@timed
def settle(amount: float) -> dict:
    time.sleep(0.01)
    return {"amount": amount, "status": "成功"}

print(settle(88.0))
print("函数名:", settle.__name__)
print("包装后的类型:", type(settle).__name__)


@dataclass
class FailingPayment:
    def pay(self, amount: float) -> dict:
        raise RuntimeError("网关超时")

@dataclass
class RetryPayment:
    inner: Payment
    attempts: int = 2
    def pay(self, amount: float) -> dict:
        for attempt in range(1, self.attempts + 1):
            try:
                return self.inner.pay(amount)
            except RuntimeError as exc:
                print(f"[重试] 第 {attempt} 次失败：{exc}")
        raise RuntimeError("重试次数已用完")

stacked = LoggedPayment(RetryPayment(FailingPayment(), attempts=2))
try:
    stacked.pay(50.0)
except RuntimeError as exc:
    print("最终结果:", exc)


working = LoggedPayment(RetryPayment(BasePayment(), attempts=2))
print(working.pay(66.0))
print("类装饰器可以自由组合，顺序决定调用顺序：外层先执行")

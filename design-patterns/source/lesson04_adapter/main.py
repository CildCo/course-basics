from dataclasses import dataclass

@dataclass
class LegacyLogger:
    def log_write(self, level: str, message: str, extra: str | None = None):
        suffix = f" | {extra}" if extra else ""
        print(f"[legacy:{level}] {message}{suffix}")

@dataclass
class LegacyPay:
    def make_charge(self, cents: int, currency: str = "CNY") -> dict:
        return {
            "ok": True,
            "charge_id": f"ch_{cents}",
            "currency": currency,
            "cents": cents,
        }

legacy_logger = LegacyLogger()
legacy_pay = LegacyPay()
legacy_logger.log_write("INFO", "订单创建", extra="order=1001")
print(legacy_pay.make_charge(9900))


from typing import Protocol

class Logger(Protocol):
    def info(self, message: str) -> None: ...
    def warn(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...

@dataclass
class LegacyLoggerAdapter:
    legacy: LegacyLogger
    def info(self, message: str) -> None:
        self.legacy.log_write("INFO", message)
    def warn(self, message: str) -> None:
        self.legacy.log_write("WARN", message)
    def error(self, message: str) -> None:
        self.legacy.log_write("ERROR", message)

def process_order(logger: Logger, order_id: str, amount: float) -> None:
    logger.info(f"订单 {order_id} 开始处理，金额 {amount:.2f}")
    if amount > 5000:
        logger.warn("金额较大，进入人工复核")
    logger.info(f"订单 {order_id} 处理完成")

process_order(LegacyLoggerAdapter(legacy_logger), "1001", 6800.0)


class PaymentGateway(Protocol):
    def pay(self, amount_yuan: float) -> dict: ...

@dataclass
class LegacyPayAdapter:
    legacy: LegacyPay
    def pay(self, amount_yuan: float) -> dict:
        cents = int(round(amount_yuan * 100))
        result = self.legacy.make_charge(cents)
        return {
            "channel": "legacy",
            "amount": amount_yuan,
            "charge_id": result["charge_id"],
            "status": "成功" if result["ok"] else "失败",
        }

def checkout(gateway: PaymentGateway, amount: float) -> dict:
    return gateway.pay(amount)

print(checkout(LegacyPayAdapter(legacy_pay), 99.0))
print(checkout(LegacyPayAdapter(legacy_pay), 1299.5))


@dataclass
class NewPayApi:
    def create_order(self, amount_yuan: float, currency: str = "CNY") -> dict:
        return {
            "success": True,
            "trade_no": f"new_{int(amount_yuan * 100)}",
            "pay_amount": amount_yuan,
            "currency": currency,
        }

@dataclass
class NewPayAdapter:
    api: NewPayApi
    def pay(self, amount_yuan: float) -> dict:
        result = self.api.create_order(amount_yuan)
        return {
            "channel": "new",
            "amount": result["pay_amount"],
            "charge_id": result["trade_no"],
            "status": "成功" if result["success"] else "失败",
        }

new_api = NewPayApi()
print("旧供应商:", checkout(LegacyPayAdapter(legacy_pay), 88.0))
print("新供应商:", checkout(NewPayAdapter(new_api), 88.0))
print("业务函数 checkout 没有变化")

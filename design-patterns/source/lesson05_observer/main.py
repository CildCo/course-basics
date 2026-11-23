from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class OrderCreated:
    order_id: str
    customer: str
    amount: float

class EventBus:
    def __init__(self):
        self._handlers: list[Callable[[OrderCreated], None]] = []

    def subscribe(self, handler):
        self._handlers.append(handler)
        return handler

    def unsubscribe(self, handler):
        if handler in self._handlers:
            self._handlers.remove(handler)

    def publish(self, event):
        for handler in list(self._handlers):
            try:
                handler(event)
            except Exception as exc:
                print(f"订阅者 {getattr(handler, '__name__', handler)} 失败：{exc}")

def sms_notify(event: OrderCreated) -> None:
    print(f"[短信] 订单 {event.order_id} 已创建，金额 {event.amount:.2f}")

def email_notify(event: OrderCreated) -> None:
    print(f"[邮件] 给 {event.customer} 发送订单确认")

def warehouse_notify(event: OrderCreated) -> None:
    print(f"[仓库] 准备拣货：订单 {event.order_id}")

bus = EventBus()
print("事件总线准备完成，当前订阅者数量:", len(bus._handlers))


bus.subscribe(sms_notify)
bus.subscribe(email_notify)
bus.subscribe(warehouse_notify)

bus.publish(OrderCreated("C001", "张三", 299.0))
print("发布结束，订阅者数量:", len(bus._handlers))


def bad_sms_gateway(event: OrderCreated) -> None:
    raise RuntimeError("短信网关超时")

bus.subscribe(bad_sms_gateway)
print("加入故障订阅者后发布：")
bus.publish(OrderCreated("C002", "李四", 128.0))
print("发布结束，其他订阅者仍然执行")


bus.unsubscribe(email_notify)
print("取消邮件订阅后发布：")
bus.publish(OrderCreated("C003", "王五", 560.0))
print("当前订阅者:", [getattr(handler, "__name__", str(handler)) for handler in bus._handlers])

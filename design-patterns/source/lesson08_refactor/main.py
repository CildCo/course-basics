from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol
import sqlite3

@dataclass(frozen=True)
class Order:
    order_id: str
    customer: str
    strategy: str
    amount: float
    payable: float
    discount: float

class DiscountStrategy(Protocol):
    name: str
    def apply(self, amount: float) -> float: ...

STRATEGY_REGISTRY = {}

def register_strategy(code):
    def wrapper(cls):
        STRATEGY_REGISTRY[code] = cls
        return cls
    return wrapper

@register_strategy("regular")
class RegularDiscount:
    name = "无折扣"
    def apply(self, amount: float) -> float:
        return round(amount, 2)

@register_strategy("member")
class MemberDiscount:
    name = "会员 95 折"
    def apply(self, amount: float) -> float:
        return round(amount * 0.95, 2)

@register_strategy("vip")
class VipDiscount:
    name = "VIP 阶梯"
    def apply(self, amount: float) -> float:
        if amount >= 2000:
            return round(amount * 0.85, 2)
        if amount >= 1000:
            return round(amount * 0.90, 2)
        return round(amount * 0.95, 2)

def create_discount(code: str) -> DiscountStrategy:
    if code not in STRATEGY_REGISTRY:
        raise ValueError(f"未知折扣策略: {code}")
    return STRATEGY_REGISTRY[code]()

print("折扣策略注册表:", sorted(STRATEGY_REGISTRY))


@dataclass(frozen=True)
class OrderPlaced:
    order: Order

class EventBus:
    def __init__(self):
        self._handlers: list[Callable[[OrderPlaced], None]] = []

    def subscribe(self, handler):
        self._handlers.append(handler)
        return handler

    def publish(self, event: OrderPlaced) -> None:
        for handler in list(self._handlers):
            try:
                handler(event)
            except Exception as exc:
                print(f"订阅者 {getattr(handler, '__name__', handler)} 失败：{exc}")

def sms_notify(event: OrderPlaced) -> None:
    print(f"[短信] {event.order.customer}，订单 {event.order.order_id} 应付 {event.order.payable:.2f}")

def warehouse_notify(event: OrderPlaced) -> None:
    print(f"[仓库] 为订单 {event.order.order_id} 锁定库存")

bus = EventBus()
bus.subscribe(sms_notify)
bus.subscribe(warehouse_notify)
print("事件总线订阅者:", [handler.__name__ for handler in bus._handlers])


class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def all(self) -> list[Order]: ...

class SQLiteOrderRepository:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    customer TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payable REAL NOT NULL,
                    discount REAL NOT NULL
                )
                """
            )

    def save(self, order: Order) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?)",
                (
                    order.order_id,
                    order.customer,
                    order.strategy,
                    order.amount,
                    order.payable,
                    order.discount,
                ),
            )

    def all(self) -> list[Order]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT order_id, customer, strategy, amount, payable, discount "
                "FROM orders ORDER BY rowid"
            ).fetchall()
        return [Order(*row) for row in rows]

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
db_path = out / "orders.db"
if db_path.exists():
    db_path.unlink()
print("SQLite 仓储准备完成:", db_path.name)


class OrderService:
    def __init__(self, strategy_factory, repository, bus):
        self.strategy_factory = strategy_factory
        self.repository = repository
        self.bus = bus

    def place(self, order_id: str, customer: str, strategy_code: str, amount: float) -> Order:
        strategy = self.strategy_factory(strategy_code)
        payable = strategy.apply(amount)
        order = Order(
            order_id=order_id,
            customer=customer,
            strategy=strategy.name,
            amount=amount,
            payable=payable,
            discount=round(amount - payable, 2),
        )
        self.repository.save(order)
        self.bus.publish(OrderPlaced(order))
        return order

    def all_orders(self) -> list[Order]:
        return self.repository.all()

service = OrderService(create_discount, SQLiteOrderRepository(db_path), bus)
print("订单服务组装完成：策略工厂 + 仓储 + 事件总线")


demo_orders = [
    ("E001", "张三", "regular", 260.0),
    ("E002", "李四", "member", 880.0),
    ("E003", "王五", "vip", 1200.0),
    ("E004", "赵六", "vip", 2600.0),
]
for order_id, customer, strategy_code, amount in demo_orders:
    order = service.place(order_id, customer, strategy_code, amount)
    print(
        f"{order.order_id} {order.customer} {order.strategy:<7} "
        f"原价 {order.amount:>7.2f} 应付 {order.payable:>7.2f} 优惠 {order.discount:>7.2f}"
    )


rows = service.all_orders()
total_amount = sum(order.amount for order in rows)
total_payable = sum(order.payable for order in rows)
total_discount = sum(order.discount for order in rows)

print("持久化订单数:", len(rows))
print(f"订单总额: {total_amount:.2f}")
print(f"实付总额: {total_payable:.2f}")
print(f"优惠总额: {total_discount:.2f}")
print("最后一条:", rows[-1])


@register_strategy("seasonal")
class SeasonalDiscount:
    name = "618 活动 88 折"
    def apply(self, amount: float) -> float:
        return round(amount * 0.88, 2)

def points_notify(event: OrderPlaced) -> None:
    points = int(event.order.payable // 10)
    print(f"[积分] 订单 {event.order.order_id} 赠送 {points} 积分")

bus.subscribe(points_notify)
order = service.place("E005", "钱七", "seasonal", 999.0)
print("新增策略与订阅者后的订单:", order.order_id, order.payable)
print("当前策略:", sorted(STRATEGY_REGISTRY))
print("当前订单数:", len(service.all_orders()))

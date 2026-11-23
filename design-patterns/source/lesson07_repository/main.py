from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import sqlite3

@dataclass(frozen=True)
class Order:
    order_id: str
    customer: str
    amount: float
    payable: float

class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def get(self, order_id: str) -> Order | None: ...
    def list_all(self) -> list[Order]: ...

class MemoryOrderRepository:
    def __init__(self):
        self._rows: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._rows[order.order_id] = order

    def get(self, order_id: str) -> Order | None:
        return self._rows.get(order_id)

    def list_all(self) -> list[Order]:
        return list(self._rows.values())

print("内存仓储准备完成，记录数:", len(MemoryOrderRepository().list_all()))


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def place(self, order_id: str, customer: str, amount: float) -> Order:
        payable = round(amount * 0.90, 2) if amount >= 1000 else round(amount, 2)
        order = Order(order_id, customer, amount, payable)
        self.repository.save(order)
        return order

    def all_orders(self) -> list[Order]:
        return self.repository.list_all()

memory_service = OrderService(MemoryOrderRepository())
for order_id, amount in [("D001", 320.0), ("D002", 1200.0)]:
    order = memory_service.place(order_id, "张三", amount)
    print(f"{order.order_id} 原价 {order.amount:.2f} 应付 {order.payable:.2f}")
print("内存中的订单数:", len(memory_service.all_orders()))


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
                    amount REAL NOT NULL,
                    payable REAL NOT NULL
                )
                """
            )

    def save(self, order: Order) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?)",
                (order.order_id, order.customer, order.amount, order.payable),
            )

    def get(self, order_id: str) -> Order | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "SELECT order_id, customer, amount, payable FROM orders WHERE order_id = ?",
                (order_id,),
            ).fetchone()
        return Order(*row) if row else None

    def list_all(self) -> list[Order]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT order_id, customer, amount, payable FROM orders ORDER BY rowid"
            ).fetchall()
        return [Order(*row) for row in rows]

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
db_path = out / "orders.db"
if db_path.exists():
    db_path.unlink()

sqlite_repo = SQLiteOrderRepository(db_path)
print("SQLite 仓储准备完成:", db_path.name)
print("当前记录数:", len(sqlite_repo.list_all()))


sqlite_service = OrderService(SQLiteOrderRepository(db_path))
sqlite_service.place("D003", "李四", 1880.0)
sqlite_service.place("D004", "王五", 260.0)

print("SQLite 订单:")
for order in sqlite_service.all_orders():
    print(order)
print("查询单条:", sqlite_service.repository.get("D003"))


def build_service(kind: str) -> OrderService:
    if kind == "memory":
        return OrderService(MemoryOrderRepository())
    if kind == "sqlite":
        return OrderService(SQLiteOrderRepository(db_path))
    raise ValueError(f"未知仓储类型: {kind}")

for kind in ["memory", "sqlite"]:
    service = build_service(kind)
    service.place(f"{kind.upper()}-001", "测试客户", 500.0)
    print(kind, "订单数:", len(service.all_orders()))

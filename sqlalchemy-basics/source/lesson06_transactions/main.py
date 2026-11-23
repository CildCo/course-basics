from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(30), unique=True)
    balance: Mapped[int] = mapped_column(default=0)


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)


def balances():
    with Session(engine) as session:
        rows = session.scalars(select(Account).order_by(Account.id))
        return {row.owner: row.balance for row in rows}


with Session(engine) as session:
    session.add_all([Account(owner="A", balance=100), Account(owner="B", balance=50)])
    session.commit()

print("初始余额:", balances())


def transfer(from_owner, to_owner, amount):
    with Session(engine) as session:
        source = session.scalar(select(Account).where(Account.owner == from_owner))
        target = session.scalar(select(Account).where(Account.owner == to_owner))
        if source.balance < amount:
            raise ValueError("余额不足")
        source.balance -= amount
        target.balance += amount
        session.commit()
        return source.balance, target.balance


print("转账后余额:", transfer("A", "B", 30))
print("当前余额:", balances())


with Session(engine) as session:
    try:
        source = session.scalar(select(Account).where(Account.owner == "B"))
        target = session.scalar(select(Account).where(Account.owner == "A"))
        source.balance -= 10_000
        target.balance += 10_000
        if source.balance < 0:
            raise ValueError("余额不足，撤销本次转账")
        session.commit()
    except ValueError as exc:
        session.rollback()
        print("已回滚:", exc)

print("当前余额:", balances())


from sqlalchemy.exc import IntegrityError, PendingRollbackError

with Session(engine) as session:
    try:
        with session.begin():
            account = session.scalar(select(Account).where(Account.owner == "A"))
            account.balance -= 10
            print("事务内余额:", account.balance)
            raise RuntimeError("下游服务失败")
    except RuntimeError as exc:
        print("上下文管理器自动回滚:", exc)

print("自动回滚后:", balances())

session = Session(engine)
try:
    session.add(Account(owner="A", balance=0))
    session.flush()
    session.commit()
except IntegrityError:
    print("唯一约束冲突，事务失败")
try:
    session.commit()
except PendingRollbackError:
    print("未回滚就再次提交会报 PendingRollbackError")
finally:
    session.rollback()
    session.close()

print("最终余额:", balances())

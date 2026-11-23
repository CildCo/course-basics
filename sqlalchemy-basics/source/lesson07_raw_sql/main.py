from datetime import date

from sqlalchemy import Date, String, create_engine, func, insert, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    amount: Mapped[int] = mapped_column(default=0)
    happened_on: Mapped[date] = mapped_column(Date, index=True)


engine = create_engine("sqlite://")
Base.metadata.create_all(engine)

seed = [
    ("order", 1200, date(2026, 1, 5)),
    ("order", 800, date(2026, 1, 18)),
    ("refund", 300, date(2026, 1, 20)),
    ("order", 1500, date(2026, 2, 3)),
    ("adjust", 200, date(2026, 2, 9)),
    ("order", 900, date(2026, 2, 14)),
    ("refund", 450, date(2026, 3, 2)),
    ("order", 1700, date(2026, 3, 11)),
    ("adjust", -100, date(2026, 3, 15)),
    ("order", 600, date(2026, 3, 22)),
]

with Session(engine) as session:
    session.add_all(
        [Event(kind=k, amount=a, happened_on=d) for k, a, d in seed]
    )
    session.commit()

print("事件数:", len(seed))
print("月份范围:", seed[0][2], "到", seed[-1][2])


monthly_sql = text("""
    SELECT substr(happened_on, 1, 7) AS month,
           COUNT(*) AS events,
           SUM(amount) AS total
    FROM events
    GROUP BY month
    ORDER BY month
""")

with engine.connect() as conn:
    for row in conn.execute(monthly_sql):
        print(f"{row.month}  {row.events:>2} 笔  {row.total:>6} 分")


summary_sql = text("""
    SELECT kind, COUNT(*) AS n, SUM(amount) AS total
    FROM events
    WHERE happened_on >= :start
    GROUP BY kind
    ORDER BY total DESC
""")

with engine.connect() as conn:
    rows = conn.execute(summary_sql, {"start": "2026-02-01"}).mappings().all()

for row in rows:
    print(dict(row))

running_sql = text("""
    SELECT id, happened_on, amount,
           SUM(amount) OVER (ORDER BY happened_on, id) AS running_total
    FROM events
    WHERE kind = :kind
    ORDER BY happened_on, id
""")

with engine.connect() as conn:
    for row in conn.execute(running_sql, {"kind": "order"}):
        print(row.happened_on, row.amount, "累计", row.running_total)


with Session(engine) as session:
    before = session.scalar(select(func.count()).select_from(Event))

    with engine.begin() as conn:
        conn.execute(
            insert(Event),
            [
                {"kind": "order", "amount": 990, "happened_on": date(2026, 10, 1)},
                {"kind": "refund", "amount": 120, "happened_on": date(2026, 10, 2)},
            ],
        )

    after = session.scalar(select(func.count()).select_from(Event))

print("批量写入前:", before)
print("批量写入后:", after)

with Session(engine) as session:
    latest = session.scalars(
        select(Event).order_by(Event.happened_on.desc()).limit(2)
    ).all()
    print("最新事件:", [(event.kind, event.amount) for event in latest])

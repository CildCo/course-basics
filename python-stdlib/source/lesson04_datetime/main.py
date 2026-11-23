from datetime import datetime

start = datetime.strptime("2026-03-01 09:30", "%Y-%m-%d %H:%M")
end = datetime.strptime("2026-03-08 18:00", "%Y-%m-%d %H:%M")
print("开始：", start.strftime("%Y-%m-%d %H:%M"))
print("结束：", end.strftime("%Y-%m-%d %H:%M"))
print("开始是周几（1=周一）：", start.isoweekday())


from datetime import timedelta

delta = end - start
print("时间差：", delta)
print("天数：", delta.days)
print("剩余秒数：", delta.seconds)
print("总秒数：", int(delta.total_seconds()))
print("提前 3 天：", (start - timedelta(days=3)).strftime("%Y-%m-%d"))


from datetime import date

day = date(2026, 3, 1)
print("加 30 天：", day + timedelta(days=30))
print("替换年份：", day.replace(year=2027))
deadline = date(2026, 4, 1)
print("距离截止还有：", (deadline - day).days, "天")


import time

start_time = time.perf_counter()
total = sum(i * i for i in range(200_000))
elapsed = time.perf_counter() - start_time
print("计算结果：", total)
print(f"耗时：{elapsed:.4f} 秒")

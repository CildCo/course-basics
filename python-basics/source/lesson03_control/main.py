score = 85

if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("需要补考")


for day in range(1, 6):
    print(f"第 {day} 天：复习 30 分钟")


total = 0
for number in range(1, 11):
    total = total + number
print("1 到 10 的和：", total)


count = 0
while True:
    count = count + 1
    if count == 3:
        break
print("循环了", count, "次")

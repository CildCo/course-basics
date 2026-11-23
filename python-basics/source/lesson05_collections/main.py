fruits = ["苹果", "香蕉", "橙子"]
print(fruits[0])
print(fruits[-1])
print(fruits[0:2])


numbers = [5, 2, 8, 1]
numbers.append(3)
numbers.remove(8)
numbers.sort()
print(numbers)
print("数量：", len(numbers))


scores = {"语文": 88, "数学": 95, "英语": 79}
scores["英语"] = 85
print(scores["数学"])
print(scores.get("物理", "没有这门课"))


for subject, score in scores.items():
    print(f"{subject}: {score}")

total = sum(scores.values())
print("平均：", round(total / len(scores), 1))

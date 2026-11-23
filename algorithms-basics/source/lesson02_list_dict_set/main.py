numbers = [10, 20, 30, 40]
print(numbers[2])
print(numbers.index(30))
print(30 in numbers)


scores = {"小居": 88, "小明": 95}
print(scores["小居"])
print(scores.get("小红", "没有记录"))
print("小明" in scores)


words = ["Python", "python", "Pandas", "pandas"]
unique = set(word.lower() for word in words)
print(unique)
print("python" in unique)

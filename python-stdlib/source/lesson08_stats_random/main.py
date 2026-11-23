from statistics import mean, median, mode, stdev

scores = [72, 85, 91, 68, 85, 79, 94]
print("平均分：", round(mean(scores), 2))
print("中位数：", median(scores))
print("众数：", mode(scores))
print("标准差：", round(stdev(scores), 2))


with_outlier = scores + [10]
print("平均分：", round(mean(with_outlier), 2))
print("中位数：", median(with_outlier))
print("标准差：", round(stdev(with_outlier), 2))


import random

random.seed(42)
print("骰子：", [random.randint(1, 6) for _ in range(8)])
print("抽样：", random.sample(range(1, 50), 6))

cards = ["A", "B", "C", "D"]
random.shuffle(cards)
print("洗牌：", cards)
print("抽一个：", random.choice(["红", "绿", "蓝"]))


random.seed(2026)
counts = {face: 0 for face in range(1, 7)}
for _ in range(1000):
    counts[random.randint(1, 6)] += 1

for face, count in counts.items():
    print(face, count)

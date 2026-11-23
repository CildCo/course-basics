text = "python is easy. python is useful. learn python step by step."
words = text.lower().replace(".", "").split()
print(words)


import heapq

counts = {}
for word in words:
    counts[word] = counts.get(word, 0) + 1

top = heapq.nlargest(3, counts.items(), key=lambda pair: pair[1])
print(top)


print("不同单词数：", len(counts))
print("总单词数：", len(words))
print("前 3 名：")
for word, count in top:
    print(word, count)

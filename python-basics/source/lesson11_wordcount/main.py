text = "Python is easy. Python is useful. Learn Python step by step."
cleaned = text.lower().replace(".", "")
words = cleaned.split()
print(words)


counts = {}
for word in words:
    counts[word] = counts.get(word, 0) + 1
print(counts)


ranked = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
print(ranked)


for index, (word, count) in enumerate(ranked[:3], 1):
    print(f"{index}. {word}: {count} 次")

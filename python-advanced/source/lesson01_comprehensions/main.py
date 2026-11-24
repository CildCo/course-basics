squares = [n * n for n in range(1, 6)]
print(squares)

lengths = {word: len(word) for word in ["Python", "NumPy", "pandas"]}
print(lengths)

unique = {word.lower() for word in ["Python", "python", "Pandas"]}
print(unique)


names = ["小李", "小明", "小红"]
scores = [88, 95, 79]
for name, score in zip(names, scores):
    print(name, score)

for index, name in enumerate(names, 1):
    print(index, name)


first, *rest = [1, 2, 3, 4]
print(first)
print(rest)

def add(a, b, c):
    return a + b + c

numbers = [1, 2, 3]
print(add(*numbers))


a, b = 1, 2
a, b = b, a
print(a, b)

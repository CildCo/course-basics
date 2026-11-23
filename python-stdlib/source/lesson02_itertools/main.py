from itertools import chain, islice

front = ["a", "b"]
back = ["c", "d"]
print(list(chain(front, back)))

squares = (n * n for n in range(10))
print("前 4 个平方数：", list(islice(squares, 4)))
print("下标 3 到 5：", list(islice(range(10), 3, 6)))


from itertools import groupby
from operator import itemgetter

rows = [
    ("drink", "coffee"),
    ("fruit", "apple"),
    ("fruit", "banana"),
    ("drink", "tea"),
    ("fruit", "cherry"),
]
rows.sort(key=itemgetter(0))

for key, group in groupby(rows, key=itemgetter(0)):
    print(key, list(group))


from itertools import combinations, product

sizes = ["S", "M"]
colors = ["red", "blue"]
pairs = [size + "-" + color for size, color in product(sizes, colors)]
print(pairs)

print(list(combinations(["a", "b", "c"], 2)))
print(list(product([0, 1], repeat=2)))

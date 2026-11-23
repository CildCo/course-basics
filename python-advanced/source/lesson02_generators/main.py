numbers = [10, 20, 30]
iterator = iter(numbers)
print(next(iterator))
print(next(iterator))
print(next(iterator))


def countdown(start):
    while start > 0:
        yield start
        start -= 1

for number in countdown(3):
    print(number)


def read_lines(text):
    for line in text.splitlines():
        yield line.strip()

for line in read_lines("第一行\n第二行\n第三行"):
    print(line)


squares = (n * n for n in range(1, 6))
print(sum(squares))
print(sum(n * n for n in range(1, 6)))

def greet(name):
    return f"你好，{name}"

message = greet("小居")
print(message)


def add(a, b=1):
    return a + b

print(add(2))
print(add(2, 5))


def stats(numbers):
    smallest = min(numbers)
    largest = max(numbers)
    average = sum(numbers) / len(numbers)
    return smallest, largest, average

low, high, avg = stats([88, 95, 79, 92])
print("最低：", low)
print("最高：", high)
print("平均：", round(avg, 1))


def is_even(number):
    return number % 2 == 0

for number in [1, 2, 3, 4]:
    print(number, is_even(number))

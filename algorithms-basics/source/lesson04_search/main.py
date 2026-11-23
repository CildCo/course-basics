def linear_search(items, target):
    steps = 0
    for index, value in enumerate(items):
        steps += 1
        if value == target:
            return index, steps
    return -1, steps

items = list(range(1, 11))
print(linear_search(items, 8))


def binary_search(items, target):
    left, right = 0, len(items) - 1
    steps = 0
    while left <= right:
        steps += 1
        middle = (left + right) // 2
        if items[middle] == target:
            return middle, steps
        if items[middle] < target:
            left = middle + 1
        else:
            right = middle - 1
    return -1, steps

print(binary_search(items, 8))


big = list(range(1, 10001))
print("线性：", linear_search(big, 9999))
print("二分：", binary_search(big, 9999))

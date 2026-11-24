def bubble_sort(items):
    data = list(items)
    comparisons = 0
    for end in range(len(data) - 1, 0, -1):
        for index in range(end):
            comparisons += 1
            if data[index] > data[index + 1]:
                data[index], data[index + 1] = data[index + 1], data[index]
    return data, comparisons

print(bubble_sort([5, 2, 4, 1, 3]))


def insertion_sort(items):
    data = list(items)
    for index in range(1, len(data)):
        current = data[index]
        position = index - 1
        while position >= 0 and data[position] > current:
            data[position + 1] = data[position]
            position -= 1
        data[position + 1] = current
    return data

print(insertion_sort([5, 2, 4, 1, 3]))


records = [{"name": "小李", "score": 88}, {"name": "小明", "score": 95}]
print(sorted(records, key=lambda row: row["score"], reverse=True))

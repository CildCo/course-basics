import bisect
import timeit
from collections import deque

VALUES = list(range(20000))
TARGETS = [(index * 66) % 20000 for index in range(300)]
VALUE_SET = set(VALUES)
SORTED = sorted(VALUES)
print("数据量:", len(VALUES), "查找次数:", len(TARGETS))


def search_list(targets):
    found = 0
    for target in targets:
        if target in VALUES:
            found += 1
    return found

def search_set(targets):
    found = 0
    for target in targets:
        if target in VALUE_SET:
            found += 1
    return found

list_time = min(timeit.repeat(lambda: search_list(TARGETS), repeat=3, number=3))
set_time = min(timeit.repeat(lambda: search_set(TARGETS), repeat=3, number=3))
print("list 查找:", round(list_time / 3 * 1000, 2), "毫秒")
print("set 查找:", round(set_time / 3 * 1000, 2), "毫秒")
print("倍数:", round(list_time / set_time, 1), "倍")


def drain_list(size):
    data = list(range(size))
    while data:
        data.pop(0)

def drain_deque(size):
    data = deque(range(size))
    while data:
        data.popleft()

list_time = min(timeit.repeat(lambda: drain_list(4000), repeat=3, number=1))
deque_time = min(timeit.repeat(lambda: drain_deque(4000), repeat=3, number=1))
print("list.pop(0):", round(list_time * 1000, 2), "毫秒")
print("deque.popleft:", round(deque_time * 1000, 2), "毫秒")
print("倍数:", round(list_time / deque_time, 1), "倍")


SEARCH_TARGETS = list(range(0, 20000, 40))

def linear_search(targets):
    found = 0
    for target in targets:
        for value in SORTED:
            if value == target:
                found += 1
                break
    return found

def bisect_search(targets):
    found = 0
    for target in targets:
        index = bisect.bisect_left(SORTED, target)
        if index < len(SORTED) and SORTED[index] == target:
            found += 1
    return found

linear_time = min(timeit.repeat(lambda: linear_search(SEARCH_TARGETS), repeat=3, number=2))
bisect_time = min(timeit.repeat(lambda: bisect_search(SEARCH_TARGETS), repeat=3, number=2))
sort_time = min(timeit.repeat(lambda: sorted(VALUES), repeat=3, number=10))
print("线性查找:", round(linear_time / 2 * 1000, 2), "毫秒")
print("二分查找:", round(bisect_time / 2 * 1000, 2), "毫秒")
print("倍数:", round(linear_time / bisect_time, 1), "倍")
print("排序一次:", round(sort_time / 10 * 1000, 2), "毫秒")

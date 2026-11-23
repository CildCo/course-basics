import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import matplotlib
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
from collections import deque


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
print("数据目录:", data_path("brackets.txt").parent.name)
print("输出目录:", out.name)


def valid_brute(text):
    pairs = ("()", "[]", "{}")
    previous = None
    while text and text != previous:
        previous = text
        for pair in pairs:
            text = text.replace(pair, "")
    return text == ""


def valid_stack(text):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for char in text:
        if char in "([{":
            stack.append(char)
        elif char in pairs:
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
        else:
            return False
    return not stack


samples = [line.strip() for line in data_path("brackets.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
for sample in samples:
    print(f"{sample!r:<12} 暴力 {valid_brute(sample)!s:<5} 栈 {valid_stack(sample)}")


cases = ["", "(", "]", "([)]", "{[()]}", "((()))", "()[]{}", "()("]
print(f"{'输入':<12}{'暴力':<8}{'栈':<8}{'一致'}")
for case in cases:
    slow = valid_brute(case)
    fast = valid_stack(case)
    print(f"{case!r:<12}{str(slow):<8}{str(fast):<8}{slow == fast}")


def window_max_brute(nums, k):
    if k <= 0 or k > len(nums):
        return []
    return [max(nums[start:start + k]) for start in range(len(nums) - k + 1)]


def window_max_deque(nums, k):
    if k <= 0 or k > len(nums):
        return []
    queue = deque()
    result = []
    for index, value in enumerate(nums):
        while queue and nums[queue[-1]] <= value:
            queue.pop()
        queue.append(index)
        if queue[0] <= index - k:
            queue.popleft()
        if index >= k - 1:
            result.append(nums[queue[0]])
    return result


nums = [1, 3, -1, -3, 5, 3, 6, 7]
for k in [1, 3, 8]:
    print(f"k={k}: 暴力 {window_max_brute(nums, k)}")
    print(f"     队列 {window_max_deque(nums, k)}")


cases = [([], 1), ([5], 1), ([5], 2), ([1, 3, -1, -3, 5, 3, 6, 7], 3), ([5, 5, 5], 2), ([-4, -2, -7], 2)]
print(f"{'输入':<34}{'k':<4}{'暴力':<26}{'队列':<26}{'一致'}")
for values, k in cases:
    slow = window_max_brute(values, k)
    fast = window_max_deque(values, k)
    print(f"{str(values):<34}{k:<4}{str(slow):<26}{str(fast):<26}{slow == fast}")


class QueueWithStacks:
    def __init__(self):
        self.inbox = []
        self.outbox = []

    def push(self, value):
        self.inbox.append(value)

    def _shift(self):
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def pop(self):
        self._shift()
        return self.outbox.pop() if self.outbox else None

    def peek(self):
        self._shift()
        return self.outbox[-1] if self.outbox else None

    def empty(self):
        return not self.inbox and not self.outbox


queue = QueueWithStacks()
queue.push(1)
queue.push(2)
queue.push(3)
print("出队:", queue.pop())
queue.push(4)
print("队头:", queue.peek())
print("依次出队:", queue.pop(), queue.pop(), queue.pop())
print("空队列出队:", queue.pop(), "是否为空:", queue.empty())

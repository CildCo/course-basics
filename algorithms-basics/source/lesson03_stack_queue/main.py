stack = []
stack.append("A")
stack.append("B")
stack.append("C")
print(stack.pop())
print(stack.pop())
print(stack)


from collections import deque

queue = deque(["A", "B", "C"])
print(queue.popleft())
print(queue.popleft())
print(queue)

a = 256
b = 256
x = int("257")
y = int("257")

print("a == b：", a == b)
print("a is b：", a is b)
print("x == y：", x == y)
print("x is y：", x is y)
print("id(a) == id(b)：", id(a) == id(b))
print("id(x) == id(y)：", id(x) == id(y))


import sys

values = [0, 256, 10 ** 30, "hello", "", [1, 2, 3], (1, 2, 3)]
for value in values:
    print(f"{type(value).__name__:6} sizeof={sys.getsizeof(value)}")


numbers = [1, 2, 3]
alias = numbers
alias.append(4)

print("numbers：", numbers)
print("numbers is alias：", numbers is alias)

copied = numbers.copy()
copied.append(5)

print("numbers：", numbers)
print("copied：", copied)
print("numbers is copied：", numbers is copied)


text = "abc"
same = text
text += "d"

print("same：", same)
print("text：", text)
print("same is text：", same is text)

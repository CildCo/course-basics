class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return f"{self.name}：汪！"

dog = Dog("豆豆", 3)
print(dog.name)
print(dog.age)
print(dog.bark())


class Counter:
    def __init__(self):
        self.value = 0

    def add(self, step=1):
        self.value += step
        return self.value

counter = Counter()
print(counter.add())
print(counter.add(3))


class Animal:
    def speak(self):
        return "某种声音"

class Cat(Animal):
    def speak(self):
        return "喵"

print(Animal().speak())
print(Cat().speak())


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Point({self.x}, {self.y})"

print(Point(2, 5))

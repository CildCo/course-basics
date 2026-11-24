def greet(name):
    return f"你好，{name}"

say = greet
print(say("小李"))
print(greet.__name__)


def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def add(a, b):
    return a + b

logged_add = log_calls(add)
print(logged_add(2, 3))


@log_calls
def multiply(a, b):
    return a * b

print(multiply(3, 4))


from functools import wraps

def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def subtract(a, b):
    """返回 a 减 b。"""
    return a - b

print(subtract(5, 2))
print(subtract.__name__)
print(subtract.__doc__)

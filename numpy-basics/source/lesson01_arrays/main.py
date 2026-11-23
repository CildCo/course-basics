import numpy as np

a = np.array([1, 2, 3, 4])
print(a)
print(a.dtype)


b = np.array([1.5, 2.5, 3.5])
print(b)
print(b.dtype)
print(np.array([1, 2], dtype=float))


print(np.zeros((2, 3)))
print(np.ones(4))


print(np.arange(0, 10, 2))
print(np.linspace(0, 1, 5))

import numpy as np

a = np.array([10, 20, 30, 40, 50])
print(a[1])
print(a[-1])
print(a[1:4])


m = np.array([[1, 2, 3], [4, 5, 6]])
print(m[0, 1])
print(m[1])
print(m[:, 1])


print(a[::2])
print(a[::-1])


print(a > 25)
print(a[a > 25])

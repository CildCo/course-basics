import numpy as np

a = np.array([[1, 2, 3], [4, 5, 6]])
print(a)
print("shape:", a.shape)
print("ndim:", a.ndim)
print("size:", a.size)


print(a.reshape(3, 2))
print(a.reshape(6))


print(a.flatten())
print(a.T)


b = np.arange(12)
print(b.reshape(3, 4).shape)
print(b.reshape(-1, 4).shape)

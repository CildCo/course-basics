import numpy as np

a = np.arange(6).reshape(2, 3)
b = np.arange(6, 12).reshape(2, 3)
print(a)
print(b)


print(np.concatenate([a, b], axis=0))
print(np.concatenate([a, b], axis=1))


stacked = np.stack([a, b], axis=0)
print(stacked.shape)
print(stacked[0])
print(stacked[1])


print(a.T)
print(a.T.shape)

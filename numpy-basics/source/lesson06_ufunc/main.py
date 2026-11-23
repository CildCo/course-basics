import numpy as np

a = np.array([1, 4, 9, 16])
print(np.sqrt(a))
print(a * 2 + 1)


scores = np.array([55, 72, 88, 100])
print(np.where(scores >= 60, "及格", "补考"))


print(np.clip(scores, 60, 90))


original = np.array([1, 2, 3])
result = np.sqrt(original)
print(original)
print(result)

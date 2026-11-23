import numpy as np

a = np.array([1, 2, 3])
print(a + 10)
print(a * 2)


column = np.array([[1], [2], [3]])
row = np.array([10, 20, 30])
result = column + row
print(result)
print(result.shape)


print(np.array([[1, 2, 3]]) + np.array([[10], [20]]))


try:
    print(np.array([1, 2, 3]) + np.array([1, 2]))
except ValueError as error:
    print("形状不匹配：", error)

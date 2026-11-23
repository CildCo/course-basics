import numpy as np

m = np.array([[1, 2, 3], [4, 5, 6]])
print(m)


print("总和：", m.sum())
print("均值：", m.mean())
print("标准差：", round(m.std(), 2))
print("最大值：", m.max())


print("按列：", m.sum(axis=0))
print("按行：", m.sum(axis=1))
print("按列均值：", m.mean(axis=0))


position = m.argmax()
print("一维位置：", position)
print("行列位置：", np.unravel_index(position, m.shape))

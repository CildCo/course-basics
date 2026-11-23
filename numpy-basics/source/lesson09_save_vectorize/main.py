import numpy as np
from pathlib import Path

output = Path("output")
output.mkdir(exist_ok=True)
a = np.arange(12).reshape(3, 4)
np.save(output / "a.npy", a)
print(a)


loaded = np.load(output / "a.npy")
print(loaded)
print(loaded.shape)


numbers = list(range(1, 6))
loop_result = [number * 2 for number in numbers]
vector_result = np.array(numbers) * 2
print(loop_result)
print(vector_result)


print(loaded % 2 == 0)
print((loaded % 2 == 0).sum())

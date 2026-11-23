import numpy as np

rng = np.random.default_rng(42)
print(rng.integers(1, 10, size=5))


print(np.round(rng.normal(0, 1, size=3), 2))


print(rng.choice(["石头", "剪刀", "布"], size=4))


rng_a = np.random.default_rng(7)
rng_b = np.random.default_rng(7)
print(rng_a.integers(0, 100, size=3))
print(rng_b.integers(0, 100, size=3))

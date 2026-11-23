def steps_constant(n):
    return 1

def steps_linear(n):
    return n

def steps_quadratic(n):
    return n * n

for n in [10, 100, 1000]:
    print(n, steps_constant(n), steps_linear(n), steps_quadratic(n))


import math

for n in [10, 100, 1000]:
    print(n, "log2:", round(math.log2(n), 2), "n log n:", round(n * math.log2(n), 1))

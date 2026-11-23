from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


rng = np.random.default_rng(20261025)
population = rng.lognormal(mean=4.3, sigma=0.8, size=20000)
true_mean = population.mean()

sample = rng.choice(population, size=100, replace=False)
xbar = sample.mean()
se = sample.std(ddof=1) / np.sqrt(len(sample))
z = norm.ppf(0.975)
ci = (xbar - z * se, xbar + z * se)

print("总体真实均值:", round(true_mean, 2))
print("样本均值:", round(xbar, 2))
print("标准误:", round(se, 2))
print("95% 置信区间:", tuple(round(float(value), 2) for value in ci))


rng = np.random.default_rng(7)
cover = 0
widths = []
for _ in range(500):
    sample = rng.choice(population, size=100, replace=False)
    mean = sample.mean()
    margin = norm.ppf(0.975) * sample.std(ddof=1) / np.sqrt(len(sample))
    cover += (mean - margin <= true_mean <= mean + margin)
    widths.append(2 * margin)

print("500 次抽样中，区间覆盖真实均值的比例:", round(cover / 500, 3))
print("平均区间宽度:", round(np.mean(widths), 2))


rng = np.random.default_rng(11)
for size in [30, 100, 400]:
    widths = []
    for _ in range(200):
        sample = rng.choice(population, size=size, replace=False)
        widths.append(2 * norm.ppf(0.975) * sample.std(ddof=1) / np.sqrt(size))
    print(f"n={size:3d}  平均区间宽度约 {np.mean(widths):6.2f}")

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


ab = pd.read_csv(data_path("ab_test.csv"))
treatment = ab.loc[ab["group"] == "treatment", "converted"].to_numpy()
control = ab.loc[ab["group"] == "control", "converted"].to_numpy()

observed = treatment.mean() - control.mean()
pooled = np.concatenate([treatment, control])
rng = np.random.default_rng(20261025)
count = 0
for _ in range(5000):
    rng.shuffle(pooled)
    diff = pooled[: len(treatment)].mean() - pooled[len(treatment) :].mean()
    if abs(diff) >= abs(observed):
        count += 1

p_value = (count + 1) / (5000 + 1)
print("实验组转化率:", f"{treatment.mean():.2%}")
print("对照组转化率:", f"{control.mean():.2%}")
print("观察到的差异:", f"{observed:.2%}")
print("置换检验 p 值:", round(p_value, 4))


rng = np.random.default_rng(42)
false_positive = 0
for _ in range(1000):
    a = rng.normal(0, 1, 200)
    b = rng.normal(0, 1, 200)
    if ttest_ind(a, b, equal_var=False).pvalue < 0.05:
        false_positive += 1

print("1000 次“其实没有差异”的实验里，p<0.05 的次数:", false_positive)
print("比例:", round(false_positive / 1000, 3))


p1 = treatment.mean()
p0 = control.mean()
absolute_lift = p1 - p0
relative_lift = absolute_lift / p0
cohen_h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p0))

se = np.sqrt(p1 * (1 - p1) / len(treatment) + p0 * (1 - p0) / len(control))
ci = (absolute_lift - 1.96 * se, absolute_lift + 1.96 * se)

print("绝对提升:", f"{absolute_lift:.2%}")
print("相对提升:", f"{relative_lift:.1%}")
print("Cohen's h:", round(cohen_h, 3))
print("差值 95% 置信区间:", tuple(round(float(value), 4) for value in ci))

from pathlib import Path

import numpy as np
import pandas as pd

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


from scipy.stats import chi2_contingency, norm, pearsonr, ttest_ind

sales = pd.read_csv(data_path("sales.csv"))
sales["amount"] = sales["units"] * sales["price"]
ab = pd.read_csv(data_path("ab_test.csv"))

east = sales.loc[sales["region"] == "华东", "amount"]
south = sales.loc[sales["region"] == "华南", "amount"]
result = ttest_ind(east, south, equal_var=False)

print("华东订单数:", len(east), "均值:", round(east.mean(), 2))
print("华南订单数:", len(south), "均值:", round(south.mean(), 2))
print("t 统计量:", round(result.statistic, 3))
print("p 值:", round(result.pvalue, 4))


table = pd.crosstab(ab["group"], ab["converted"])
chi2, p_value, dof, expected = chi2_contingency(table, correction=False)

print("列联表:")
print(table)
print("卡方统计量:", round(chi2, 3))
print("自由度:", dof)
print("p 值:", round(p_value, 4))
print("期望频数:")
print(pd.DataFrame(expected, index=table.index, columns=table.columns).round(2))


r, p_value = pearsonr(sales["price"], sales["units"])
print("价格与数量相关系数:", round(r, 3))
print("p 值:", round(p_value, 4))
print("样本量:", len(sales))


z = norm.ppf(0.975)
print("95% 双侧正态临界值:", round(z, 3))
print("P(Z <= 1.96):", round(norm.cdf(1.96), 4))
print("标准正态 95% 区间:", tuple(round(float(value), 3) for value in norm.interval(0.95)))

p = 0.12
margin = 0.02
required = (z ** 2 * p * (1 - p)) / margin ** 2
print("估计 12% 转化率、允许 2 个百分点误差所需样本量:", int(np.ceil(required)))

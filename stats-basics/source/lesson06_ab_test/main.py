from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


ab = pd.read_csv(data_path("ab_test.csv"))

summary = ab.groupby("group").agg(
    users=("user_id", "size"),
    conversions=("converted", "sum"),
    conversion_rate=("converted", "mean"),
    revenue_per_user=("revenue", "mean"),
)
summary["revenue_per_converter"] = (
    ab.loc[ab["converted"] == 1].groupby("group")["revenue"].mean()
)
summary.round(4)


control = ab.loc[ab["group"] == "control", "converted"]
treatment = ab.loc[ab["group"] == "treatment", "converted"]

p0 = control.mean()
p1 = treatment.mean()
absolute_lift = p1 - p0
relative_lift = absolute_lift / p0

se = np.sqrt(p1 * (1 - p1) / len(treatment) + p0 * (1 - p0) / len(control))
ci = (absolute_lift - 1.96 * se, absolute_lift + 1.96 * se)

table = pd.crosstab(ab["group"], ab["converted"])
chi2, p_value, dof, expected = chi2_contingency(table, correction=False)

print("对照组转化率:", f"{p0:.2%}")
print("实验组转化率:", f"{p1:.2%}")
print("绝对提升:", f"{absolute_lift:.2%}")
print("相对提升:", f"{relative_lift:.1%}")
print("95% 置信区间:", tuple(round(float(value), 4) for value in ci))
print("卡方检验 p 值:", round(p_value, 4))


revenue_treatment = ab.loc[ab["group"] == "treatment", "revenue"]
revenue_control = ab.loc[ab["group"] == "control", "revenue"]
result = ttest_ind(revenue_treatment, revenue_control, equal_var=False)

difference = revenue_treatment.mean() - revenue_control.mean()
se_revenue = np.sqrt(
    revenue_treatment.var(ddof=1) / len(revenue_treatment)
    + revenue_control.var(ddof=1) / len(revenue_control)
)
revenue_ci = (difference - 1.96 * se_revenue, difference + 1.96 * se_revenue)

print("实验组每用户收入:", round(revenue_treatment.mean(), 2))
print("对照组每用户收入:", round(revenue_control.mean(), 2))
print("收入差:", round(difference, 2))
print("收入差 95% 置信区间:", tuple(round(float(value), 2) for value in revenue_ci))
print("Welch t 检验 p 值:", round(result.pvalue, 4))


if ci[0] > 0:
    decision = "转化率提升有统计支持，可以考虑扩大流量并继续观察收入"
elif ci[1] < 0:
    decision = "转化率下降有统计支持，应停止实验并排查原因"
else:
    decision = "置信区间跨 0，当前样本不足以确认提升，建议延长实验或扩大样本"

print("业务结论:", decision)
print("下一步：先不要全量上线；把实验周期至少覆盖一个完整周，并按渠道检查样本是否均衡。")

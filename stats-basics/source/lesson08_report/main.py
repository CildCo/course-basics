import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, norm, pearsonr, ttest_ind

def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)


sales = pd.read_csv(data_path("sales.csv"))
sales["amount"] = sales["units"] * sales["price"]
ab = pd.read_csv(data_path("ab_test.csv"))

control = ab.loc[ab["group"] == "control", "converted"]
treatment = ab.loc[ab["group"] == "treatment", "converted"]
p0 = control.mean()
p1 = treatment.mean()
n0 = len(control)
n1 = len(treatment)
difference = p1 - p0
relative_lift = difference / p0
se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
ci_low, ci_high = difference - norm.ppf(0.975) * se, difference + norm.ppf(0.975) * se
cohen_h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p0))

table = pd.crosstab(ab["group"], ab["converted"])
chi2, p_value, dof, expected = chi2_contingency(table, correction=False)

revenue_t = ab.loc[ab["group"] == "treatment", "revenue"]
revenue_c = ab.loc[ab["group"] == "control", "revenue"]
revenue_result = ttest_ind(revenue_t, revenue_c, equal_var=False)

print("订单数:", len(sales))
print("客单价中位数:", round(sales["amount"].median(), 2))
print("客单价均值:", round(sales["amount"].mean(), 2))
print("对照组转化率:", f"{p0:.2%}", "实验组转化率:", f"{p1:.2%}")
print("绝对提升:", f"{difference:.2%}", "95% CI:", f"[{ci_low:.2%}, {ci_high:.2%}]")
print("卡方 p 值:", round(p_value, 4), "Cohen's h:", round(cohen_h, 3))
print("每用户收入差:", round(revenue_t.mean() - revenue_c.mean(), 2), "p 值:", round(revenue_result.pvalue, 4))


from IPython.display import Image, display
import matplotlib.pyplot as plt

rates = [p0, p1]
errors = [norm.ppf(0.975) * np.sqrt(rate * (1 - rate) / size) for rate, size in [(p0, n0), (p1, n1)]]

fig, ax = plt.subplots(figsize=(6.5, 4))
bars = ax.bar(["对照组", "实验组"], rates, yerr=errors, capsize=8, color=["#9aa5b1", "#4f7cff"], width=0.5)
for bar, rate in zip(bars, rates):
    ax.text(bar.get_x() + bar.get_width() / 2, rate + 0.006, f"{rate:.2%}", ha="center", fontsize=11)
ax.set_ylim(0, max(rates) * 1.45)
ax.set_ylabel("转化率")
ax.set_title("转化率与 95% 置信区间")
fig.tight_layout()
fig.savefig(out / "ab-conversion.png", dpi=120)
display(Image(filename=str(out / "ab-conversion.png")))


report = f"""# A/B 测试统计报告

## 一、结论

实验组转化率为 {p1:.2%}，对照组为 {p0:.2%}，绝对提升 {difference:.2%}，相对提升 {relative_lift:.1%}。
差值的 95% 置信区间为 [{ci_low:.2%}, {ci_high:.2%}]，卡方检验 p 值为 {p_value:.4f}。
区间跨过 0，当前样本不足以确认提升，建议延长实验或扩大样本，暂不全量上线。

## 二、数据与口径

- 样本量：{n0 + n1} 名用户，对照组 {n0} 人，实验组 {n1} 人
- 观察窗口：2026-09-01 至 2026-10-20
- 主指标：转化率（converted 的均值）
- 辅助指标：每用户收入（revenue 的均值）
- 描述统计参考：{len(sales)} 条销售记录，客单价均值 {sales['amount'].mean():.2f} 元，中位数 {sales['amount'].median():.2f} 元

## 三、统计结果

- 绝对提升：{difference:.2%}
- 相对提升：{relative_lift:.1%}
- 差值 95% 置信区间：[{ci_low:.2%}, {ci_high:.2%}]
- 卡方检验：chi2={chi2:.3f}，自由度={dof}，p={p_value:.4f}
- 效应量 Cohen's h：{cohen_h:.3f}
- 每用户收入差：{revenue_t.mean() - revenue_c.mean():.2f} 元，Welch t 检验 p={revenue_result.pvalue:.4f}

## 四、业务解释

转化率的点估计是正的，但不确定性很大。按当前数据，实验组可能比对照组高 4 个百分点，也可能略低。
每用户收入的差异同样不显著，且收入分布有长尾，不能只看均值。

## 五、局限性

- 只覆盖一个 50 天的窗口，未验证长期效果和新鲜感消退
- 未按渠道、新老用户分层，整体结果可能掩盖局部差异
- 收入长尾明显，均值对少数大额订单敏感
- 未记录实验前的样本量计算和主指标锁定过程
- 多次查看数据或比较多个指标都会增加假阳性风险

## 六、下一步

1. 延长实验周期，覆盖至少一个完整周和一次促销节点
2. 实验前锁定主指标和样本量，避免中途决策
3. 按渠道分层检查提升是否集中，但注意分层后的样本量
4. 同时监控客诉、退款等护栏指标
"""

(out / "statistics-report.md").write_text(report, encoding="utf-8")
print(report)

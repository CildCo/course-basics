from pathlib import Path
import math

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from scipy import stats
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)
print("课程数据目录:", data_path("ab_test_users.csv").parent.name)
print("输出目录:", out.name)


users = pd.read_csv(data_path("ab_test_users.csv"))
control = users[users["group"] == "control"]
treatment = users[users["group"] == "treatment"]

print("实验名称：落地页新版注册转化实验")
print("分析人群：随机进入实验的全部用户")
print("主指标：注册转化率")
print("护栏指标：7 日留存率、人均停留时长")
print("样本量:", len(users), "（对照", len(control), "，实验", len(treatment), "）")

observed = users["group"].value_counts().reindex(["control", "treatment"]).to_numpy()
expected = np.array([len(users) / 2, len(users) / 2])
chi2, p_srm = stats.chisquare(observed, expected)
print("SRM 检查 p 值:", round(float(p_srm), 4))
print("缺失值总数:", int(users.isna().sum().sum()))


x1 = int(control["converted"].sum())
x2 = int(treatment["converted"].sum())
n1 = len(control)
n2 = len(treatment)
p1 = x1 / n1
p2 = x2 / n2
pooled = (x1 + x2) / (n1 + n2)
se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
z_score = (p2 - p1) / se_pooled
p_value = 2 * stats.norm.sf(abs(z_score))

diff = p2 - p1
se_unpooled = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
z_crit = stats.norm.ppf(0.975)
ci_low = diff - z_crit * se_unpooled
ci_high = diff + z_crit * se_unpooled

print("对照组转化率:", f"{p1:.2%}", f"({x1}/{n1})")
print("实验组转化率:", f"{p2:.2%}", f"({x2}/{n2})")
print("绝对提升:", f"{diff:.2%}")
print("相对提升:", f"{diff / p1:.1%}")
print("z 值:", round(float(z_score), 3))
print("双侧 p 值:", round(float(p_value), 4))
print("95% 置信区间:", f"[{ci_low:.2%}, {ci_high:.2%}]")


def prop_test_p(x1, n1, x2, n2):
    p1 = x1 / n1
    p2 = x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    z_score = (p2 - p1) / se
    return 2 * stats.norm.sf(abs(z_score))


retention_p = prop_test_p(
    int(control["retained_7d"].sum()), n1,
    int(treatment["retained_7d"].sum()), n2,
)
session_p = stats.ttest_ind(control["session_seconds"], treatment["session_seconds"], equal_var=False).pvalue

guardrail = pd.DataFrame(
    [
        ["7 日留存率", control["retained_7d"].mean(), treatment["retained_7d"].mean(), retention_p],
        ["人均停留时长", control["session_seconds"].mean(), treatment["session_seconds"].mean(), session_p],
    ],
    columns=["指标", "对照组", "实验组", "p 值"],
)
guardrail["p 值"] = guardrail["p 值"].round(4)
display(guardrail)

print("按设备分层:")
for device in ["mobile", "desktop"]:
    part = users[users["device"] == device]
    rates = part.groupby("group")["converted"].mean()
    print(
        f"  {device}: 对照 {rates['control']:.2%}，"
        f"实验 {rates['treatment']:.2%}，"
        f"差 {rates['treatment'] - rates['control']:+.2%}"
    )


fig, ax = plt.subplots(figsize=(7.6, 4.4))
groups = ["对照组", "实验组"]
rates = [p1, p2]
errors = [
    z_crit * math.sqrt(p1 * (1 - p1) / n1),
    z_crit * math.sqrt(p2 * (1 - p2) / n2),
]
colors = ["#4C78A8", "#E45756"]
ax.bar(groups, rates, yerr=errors, capsize=8, color=colors, width=0.52)
ax.set_ylabel("注册转化率")
ax.set_title("落地页实验：转化率与 95% 置信区间")
ax.set_ylim(0, 0.28)
ax.spines[["top", "right"]].set_visible(False)
for i, value in enumerate(rates):
    ax.text(i, value + errors[i] + 0.008, f"{value:.1%}", ha="center", fontsize=10)
fig.tight_layout()
fig.savefig(out / "final-conversion.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "final-conversion.png")))
plt.close(fig)


report = f"""# 落地页 A/B 实验分析报告

## 1. 设计与口径

- 实验问题：新版落地页是否提高注册转化率。
- 主指标：注册转化率 = 注册人数 / 进入落地页用户数。
- 护栏指标：7 日留存率、人均停留时长。
- 分析人群：随机进入实验的全部用户。

## 2. 数据检查

- 总样本量：{len(users)}（对照 {n1}，实验 {n2}）。
- SRM 检查：p = {p_srm:.4f}，未发现分组比例失衡。
- 缺失值：{int(users.isna().sum().sum())} 个。

## 3. 主指标结果

- 对照组转化率：{p1:.2%}（{x1}/{n1}）。
- 实验组转化率：{p2:.2%}（{x2}/{n2}）。
- 绝对提升：{diff:.2%}；相对提升：{diff / p1:.1%}。
- 两比例 z 检验：z = {z_score:.3f}，双侧 p = {p_value:.4f}。
- 提升的 95% 置信区间：[{ci_low:.2%}, {ci_high:.2%}]。

## 4. 护栏指标

- 7 日留存率：对照 {control['retained_7d'].mean():.2%}，实验 {treatment['retained_7d'].mean():.2%}，p = {retention_p:.4f}。
- 人均停留时长：对照 {control['session_seconds'].mean():.1f} 秒，实验 {treatment['session_seconds'].mean():.1f} 秒，p = {session_p:.4f}。
- 两项护栏指标均未发现显著恶化。

## 5. 分层结果

- 移动端：对照 {users[(users['device'] == 'mobile') & (users['group'] == 'control')]['converted'].mean():.2%}，实验 {users[(users['device'] == 'mobile') & (users['group'] == 'treatment')]['converted'].mean():.2%}。
- 桌面端：对照 {users[(users['device'] == 'desktop') & (users['group'] == 'control')]['converted'].mean():.2%}，实验 {users[(users['device'] == 'desktop') & (users['group'] == 'treatment')]['converted'].mean():.2%}。
- 两个设备分层方向一致。

## 6. 结论与建议

- 结论：新版落地页对注册转化率有正向效果，点估计约提升 {diff:.2%}，95% 区间下限为 {ci_low:.2%}。
- 建议：可以灰度放量，同时继续监控留存和投诉；放量后观察至少一个完整留存周期。
- 边界：本实验只覆盖注册转化，不能直接推断付费、长期留存或品牌影响；区间下限较小，收益规模仍需业务判断。
- 后续：如果希望确认 2 个百分点以内的小提升，需要按第 5 课的方法重新估算样本量。
"""

(out / "ab-testing-report.md").write_text(report, encoding="utf-8")
print(report)
print("报告已保存:", out / "ab-testing-report.md")

import matplotlib
matplotlib.use("Agg")

from pathlib import Path

import time

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, brier_score_loss, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedKFold, cross_val_predict, train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(1 - data.target, name="malignant")

X_tmp, X_test, y_tmp, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
X_train, X_valid, y_train, y_valid = train_test_split(
    X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=RANDOM_STATE
)
print("训练:", X_train.shape, "验证:", X_valid.shape, "测试:", X_test.shape)
print("恶性比例 训练/验证/测试:",
      round(float(y_train.mean()), 3),
      round(float(y_valid.mean()), 3),
      round(float(y_test.mean()), 3))


def fit_candidates():
    candidates = {
        "Dummy（多数类）": DummyClassifier(strategy="prior"),
        "逻辑回归": Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ]),
        "随机森林": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=1,
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=120, learning_rate=0.05, num_leaves=15,
            min_child_samples=20, random_state=RANDOM_STATE,
            n_jobs=1, force_col_wise=True, verbose=-1,
        ),
    }
    rows = []
    for name, model in candidates.items():
        start = time.perf_counter()
        model.fit(X_train, y_train)
        seconds = time.perf_counter() - start
        prob = model.predict_proba(X_valid)[:, 1]
        rows.append({
            "模型": name,
            "验证 AUC": roc_auc_score(y_valid, prob),
            "验证 Brier": brier_score_loss(y_valid, prob),
            "拟合耗时（秒）": seconds,
            "模型对象": model,
        })
    return pd.DataFrame(rows)


candidate_table = fit_candidates()
candidate_table.drop(columns="模型对象").round(4)


best_row = candidate_table.sort_values("验证 AUC", ascending=False).iloc[0]
best_name = best_row["模型"]
best_model = best_row["模型对象"]
valid_prob = best_model.predict_proba(X_valid)[:, 1]

FN_COST, FP_COST = 10, 2


def cost_of(y_true, prob, threshold):
    pred = (prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
    return int(fn * FN_COST + fp * FP_COST), int(fn), int(fp)


thresholds = np.arange(0.05, 0.96, 0.01)
valid_costs = np.array([cost_of(y_valid, valid_prob, t)[0] for t in thresholds])
valid_best = float(thresholds[valid_costs.argmin()])

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
oof_prob = cross_val_predict(
    best_model, X_train, y_train, cv=skf, method="predict_proba"
)[:, 1]
oof_costs = np.array([cost_of(y_train, oof_prob, t)[0] for t in thresholds])
candidates = thresholds[oof_costs == oof_costs.min()]
best_threshold = float(candidates[np.argmin(np.abs(candidates - 0.5))])

print("验证集选中模型:", best_name)
print("验证集最低成本阈值:", round(valid_best, 2), "成本:", cost_of(y_valid, valid_prob, valid_best))
print("训练集袋外阈值:", round(best_threshold, 2), "袋外成本:", cost_of(y_train, oof_prob, best_threshold))

threshold_compare = pd.DataFrame([
    {
        "口径": "验证集",
        "阈值": round(valid_best, 2),
        "成本": cost_of(y_valid, valid_prob, valid_best)[0],
        "漏报": cost_of(y_valid, valid_prob, valid_best)[1],
        "误报": cost_of(y_valid, valid_prob, valid_best)[2],
    },
    {
        "口径": "训练集 5 折袋外",
        "阈值": round(best_threshold, 2),
        "成本": cost_of(y_train, oof_prob, best_threshold)[0],
        "漏报": cost_of(y_train, oof_prob, best_threshold)[1],
        "误报": cost_of(y_train, oof_prob, best_threshold)[2],
    },
])
threshold_compare


test_prob = best_model.predict_proba(X_test)[:, 1]

def report_metrics(threshold):
    pred = (test_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    return {
        "阈值": round(float(threshold), 2),
        "准确率": accuracy_score(y_test, pred),
        "精确率": precision_score(y_test, pred, zero_division=0),
        "召回率": recall_score(y_test, pred, zero_division=0),
        "F1": f1_score(y_test, pred, zero_division=0),
        "AUC": roc_auc_score(y_test, test_prob),
        "Brier": brier_score_loss(y_test, test_prob),
        "漏报": int(fn),
        "误报": int(fp),
        "成本": int(fn * FN_COST + fp * FP_COST),
    }

final_table = pd.DataFrame([
    report_metrics(0.5),
    report_metrics(best_threshold),
])
print("测试集 AUC（与阈值无关）:", round(float(roc_auc_score(y_test, test_prob)), 4))
final_table.round(3)


import matplotlib
import matplotlib.pyplot as plt
from IPython.display import Image, display

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

perm = permutation_importance(
    best_model, X_test, y_test,
    n_repeats=10, random_state=RANDOM_STATE,
    scoring="roc_auc", n_jobs=1,
)
importance = pd.DataFrame({
    "特征": X.columns,
    "置换重要性": perm.importances_mean,
    "波动": perm.importances_std,
}).sort_values("置换重要性", ascending=False).head(6)

fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(importance["特征"][::-1], importance["置换重要性"][::-1], color="#5B7DB1")
ax.set_xlabel("AUC 下降幅度")
ax.set_title("测试集置换重要性（前六）")
ax.grid(axis="x", alpha=0.25)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUTPUT / "project-importance.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(OUTPUT / "project-importance.png")))
plt.close(fig)
importance.round(4)


top_features = "、".join(importance["特征"].head(3))
default_row = final_table.iloc[0]
tuned_row = final_table.iloc[1]

report = f'''# 乳腺癌筛查辅助模型报告

## 数据
- 样本数：{len(X)}，特征数：{X.shape[1]}
- 切分：训练 {len(X_train)} / 验证 {len(X_valid)} / 测试 {len(X_test)}，分层抽样
- 标签：1 表示恶性，恶性比例约 {y.mean():.1%}

## 模型选择
- 候选：Dummy、逻辑回归、随机森林、LightGBM
- 验证集 AUC 最高：{best_name}（{best_row['验证 AUC']:.4f}）
- 业务代价：漏报 {FN_COST}，误报 {FP_COST}

## 测试集结果
- 默认阈值 0.50：准确率 {default_row['准确率']:.3f}，召回率 {default_row['召回率']:.3f}，AUC {default_row['AUC']:.3f}，成本 {default_row['成本']}
- 袋外阈值 {best_threshold:.2f}：准确率 {tuned_row['准确率']:.3f}，召回率 {tuned_row['召回率']:.3f}，AUC {tuned_row['AUC']:.3f}，成本 {tuned_row['成本']}

## 阈值选择
- 验证集只有 {len(X_valid)} 条，最低成本阈值 {valid_best:.2f} 落在很宽的并列区间里，稳定性不足
- 最终阈值由训练集 5 折袋外概率选出，每条样本的预测都来自没见过它的模型

## 主要特征
- 置换重要性前三位：{top_features}
- 这些特征反映细胞核的形态和纹理，与恶性程度相关，但不构成因果结论

## 适用边界
- 数据来自单一来源、样本量有限，换医院或换设备需要重新验证
- 模型只做辅助筛查，不能替代病理诊断
- 阈值按当前漏报/误报代价设定，业务代价变化时应重新选择
'''

(OUTPUT / "report.md").write_text(report, encoding="utf-8")
print(report)
print("报告已写入:", OUTPUT / "report.md")

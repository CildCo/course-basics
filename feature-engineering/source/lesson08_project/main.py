from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
from IPython.display import Image, display

SEED = 42
np.random.seed(SEED)


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

SNAPSHOT = pd.Timestamp("2025-06-30")

df = pd.read_csv(data_path("customer_churn.csv"), parse_dates=["signup_date"])
df["support_notes"] = df["support_notes"].fillna("")
df["signup_month"] = df["signup_date"].dt.month
df["signup_weekday"] = df["signup_date"].dt.weekday
df["is_weekend"] = (df["signup_weekday"] >= 5).astype(int)
df["tenure_days"] = (SNAPSHOT - df["signup_date"]).dt.days

usage = pd.read_csv(data_path("usage_monthly.csv"), parse_dates=["month"])
agg = usage.groupby("customer_id").agg(
    usage_mean_6m=("usage_gb", "mean"),
    usage_std_6m=("usage_gb", "std"),
    usage_max_6m=("usage_gb", "max"),
    active_months=("usage_gb", "count"),
).reset_index()
pivot = usage.pivot(index="customer_id", columns="month", values="usage_gb").sort_index(axis=1)
trend = (pivot.iloc[:, -3:].mean(axis=1) / pivot.iloc[:, :3].mean(axis=1) - 1).rename("usage_trend").reset_index()
agg = agg.merge(trend, on="customer_id")
df = df.merge(agg, on="customer_id", how="left")

print("客户数:", len(df), "流失率:", f"{df['churned'].mean():.1%}")
print("窗口特征缺失:", int(df["usage_trend"].isna().sum()))
display(df[["customer_id", "signup_date", "usage_mean_6m", "usage_trend", "support_notes", "churned"]].head(4))


from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

numeric_cols = [
    "age", "tenure_months", "monthly_fee", "monthly_usage_gb",
    "support_calls", "last_login_days_ago",
]
categorical_cols = [
    "region", "city", "plan", "contract_type", "payment_method", "auto_renew",
]
time_cols = ["signup_month", "signup_weekday", "is_weekend", "tenure_days"]
window_cols = ["usage_mean_6m", "usage_std_6m", "usage_max_6m", "usage_trend", "active_months"]
text_col = "support_notes"


def build_pipeline(num_cols, cat_cols, use_text):
    transformers = []
    if num_cols:
        transformers.append(("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), num_cols))
    if cat_cols:
        transformers.append(("cat", Pipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), cat_cols))
    if use_text:
        transformers.append(("text", TfidfVectorizer(
            max_features=300, ngram_range=(1, 2), min_df=3
        ), text_col))
    pre = ColumnTransformer(transformers)
    return Pipeline([
        ("pre", pre),
        ("model", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])


train, test = train_test_split(
    df, test_size=0.25, stratify=df["churned"], random_state=SEED
)
print("训练集:", len(train), "测试集:", len(test))
print("训练集流失率:", f"{train['churned'].mean():.1%}", "测试集流失率:", f"{test['churned'].mean():.1%}")


stages = [
    ("A 数值", numeric_cols, [], False),
    ("B +类别编码", numeric_cols, categorical_cols, False),
    ("C +时间与窗口", numeric_cols + time_cols + window_cols, categorical_cols, False),
    ("D +文本", numeric_cols + time_cols + window_cols, categorical_cols, True),
]
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

rows = []
for name, num_cols, cat_cols, use_text in stages:
    pipeline = build_pipeline(num_cols, cat_cols, use_text)
    scores = cross_val_score(
        pipeline, train, train["churned"], cv=cv, scoring="roc_auc"
    )
    rows.append({
        "阶段": name,
        "AUC 均值": round(scores.mean(), 4),
        "AUC 标准差": round(scores.std(), 4),
    })

ablation = pd.DataFrame(rows)
ablation["较上一阶段"] = ablation["AUC 均值"].diff().round(4)
display(ablation)


fig, ax = plt.subplots(figsize=(7.8, 4.2))
colors = ["#9AA5B1", "#7A9CC6", "#4C78A8", "#2F5D8A"]
bars = ax.bar(
    ablation["阶段"],
    ablation["AUC 均值"],
    yerr=ablation["AUC 标准差"],
    capsize=4,
    color=colors,
    width=0.55,
)
for bar, value in zip(bars, ablation["AUC 均值"]):
    ax.text(bar.get_x() + bar.get_width() / 2, value + 0.012, f"{value:.3f}",
            ha="center", va="bottom", fontsize=9)
ax.set_ylim(0.5, max(ablation["AUC 均值"]) + 0.06)
ax.set_ylabel("交叉验证 ROC AUC")
ax.set_title("特征消融：每一步加了多少")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "ablation.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "ablation.png")))
plt.close(fig)
print("相对基线提升:", round(float(ablation["AUC 均值"].iloc[-1] - ablation["AUC 均值"].iloc[0]), 4))


from sklearn.metrics import classification_report, roc_auc_score

final_model = build_pipeline(
    numeric_cols + time_cols + window_cols, categorical_cols, True
)
final_model.fit(train, train["churned"])
test_proba = final_model.predict_proba(test)[:, 1]
test_auc = roc_auc_score(test["churned"], test_proba)
predictions = (test_proba >= 0.5).astype(int)

print("最终模型测试 AUC:", round(test_auc, 4))
print("分类报告:")
print(classification_report(
    test["churned"], predictions, target_names=["留存", "流失"], zero_division=0
))

pre = final_model.named_steps["pre"]
coefficients = pd.Series(
    final_model.named_steps["model"].coef_[0],
    index=pre.get_feature_names_out(),
).sort_values()
print("最推向流失的特征:")
print(coefficients.tail(5).round(3).to_string())
print("最推向留存的特征:")
print(coefficients.head(5).round(3).to_string())

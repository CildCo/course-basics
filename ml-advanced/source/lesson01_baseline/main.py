from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
OUTPUT = Path.cwd() / "output"
OUTPUT.mkdir(exist_ok=True)

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(1 - data.target, name="malignant")

print("样本数:", X.shape[0])
print("特征数:", X.shape[1])
print("恶性比例:", round(float(y.mean()), 3))


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
)
print("训练集:", X_train.shape, "测试集:", X_test.shape)

def evaluate(name, model):
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    return {
        "模型": name,
        "准确率": accuracy_score(y_test, pred),
        "召回率": recall_score(y_test, pred),
        "AUC": roc_auc_score(y_test, prob),
        "漏报": fn,
        "误报": fp,
    }

logistic = Pipeline([
    ("scale", StandardScaler()),
    ("clf", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
])

results = pd.DataFrame([
    evaluate("Dummy（多数类）", DummyClassifier(strategy="prior")),
    evaluate("Dummy（按比例随机）", DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)),
    evaluate("逻辑回归", logistic),
])
results.round(3)


FN_COST = 10
FP_COST = 2
logistic.fit(X_train, y_train)
prob = logistic.predict_proba(X_test)[:, 1]

rows = []
for threshold in np.arange(0.10, 0.91, 0.05):
    pred = (prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
    rows.append({
        "阈值": round(float(threshold), 2),
        "漏报": int(fn),
        "误报": int(fp),
        "业务成本": int(fn * FN_COST + fp * FP_COST),
    })

cost_table = pd.DataFrame(rows)
best = cost_table.loc[cost_table["业务成本"].idxmin()]
print("默认阈值 0.50 的成本:", int(cost_table.loc[cost_table["阈值"] == 0.50, "业务成本"].iloc[0]))
print("最低成本阈值:", best["阈值"], "成本:", best["业务成本"])
cost_table.head(8)

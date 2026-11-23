from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

cancer = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    cancer.data, cancer.target, test_size=0.2, random_state=42, stratify=cancer.target
)

clf = LogisticRegression(max_iter=5000, random_state=42).fit(X_train, y_train)
pred = clf.predict(X_test)
proba = clf.predict_proba(X_test)[:, 1]

print("准确率:", round(accuracy_score(y_test, pred), 3))
print("精确率:", round(precision_score(y_test, pred), 3))
print("召回率:", round(recall_score(y_test, pred), 3))
print("F1:", round(f1_score(y_test, pred), 3))
print("ROC AUC:", round(roc_auc_score(y_test, proba), 3))


from sklearn.metrics import confusion_matrix

cm = confusion_matrix(y_test, pred)
tn, fp, fn, tp = cm.ravel()

print("TN:", tn, "FP:", fp, "FN:", fn, "TP:", tp)
print("手算精确率:", round(tp / (tp + fp), 3))
print("手算召回率:", round(tp / (tp + fn), 3))
print("手算准确率:", round((tp + tn) / (tp + tn + fp + fn), 3))


from sklearn.dummy import DummyClassifier

majority = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
dummy_pred = majority.predict(X_test)

print("多数类基线准确率:", round(accuracy_score(y_test, dummy_pred), 3))
print("多数类基线对良性类的召回率:", round(recall_score(y_test, dummy_pred, zero_division=0), 3))
print("多数类基线对恶性类的召回率:", round(recall_score(y_test, dummy_pred, pos_label=0, zero_division=0), 3))
print("基线预测为良性的样本数:", int((dummy_pred == 1).sum()))
print("测试集真实良性样本数:", int((y_test == 1).sum()))

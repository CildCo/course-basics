from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

cancer = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    cancer.data, cancer.target, test_size=0.2, random_state=42, stratify=cancer.target
)

clf = LogisticRegression(max_iter=5000, random_state=42)
clf.fit(X_train, y_train)
pred = clf.predict(X_test)

print("类别顺序:", clf.classes_)
print("测试集准确率:", round(clf.score(X_test, y_test), 3))


proba = clf.predict_proba(X_test[:5])

for i, (probs, label) in enumerate(zip(proba, y_test[:5])):
    print(
        f"样本{i}: 恶性={probs[0]:.3f} 良性={probs[1]:.3f} "
        f"预测={int(pred[i])} 真实={label}"
    )


from sklearn.metrics import confusion_matrix, classification_report

cm = confusion_matrix(y_test, pred)
print("混淆矩阵 [[TN, FP], [FN, TP]]:")
print(cm)
print()
print(classification_report(y_test, pred, target_names=cancer.target_names))

from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
import numpy as np

diabetes = load_diabetes()
X, y = diabetes.data, diabetes.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("训练集:", X_train.shape, "测试集:", X_test.shape)
print("目标值范围:", round(float(y.min()), 1), "到", round(float(y.max()), 1))
print("训练集均值:", round(float(y_train.mean()), 1))
print("测试集均值:", round(float(y_test.mean()), 1))


from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

baseline = DummyRegressor(strategy="mean")
baseline.fit(X_train, y_train)
pred = baseline.predict(X_test)

print("基线 MAE:", round(mean_absolute_error(y_test, pred), 2))
print("基线 RMSE:", round(root_mean_squared_error(y_test, pred), 2))
print("基线 R2:", round(r2_score(y_test, pred), 3))


from sklearn.datasets import load_breast_cancer
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score

cancer = load_breast_cancer()
Xc_train, Xc_test, yc_train, yc_test = train_test_split(
    cancer.data, cancer.target, test_size=0.2, random_state=42, stratify=cancer.target
)

majority = DummyClassifier(strategy="most_frequent")
majority.fit(Xc_train, yc_train)
pred_c = majority.predict(Xc_test)

print("训练集类别分布:", np.bincount(yc_train))
print("测试集类别分布:", np.bincount(yc_test))
print("多数类基线准确率:", round(accuracy_score(yc_test, pred_c), 3))

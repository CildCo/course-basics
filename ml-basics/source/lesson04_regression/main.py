import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

diabetes = load_diabetes()
X_train, X_test, y_train, y_test = train_test_split(
    diabetes.data, diabetes.target, test_size=0.2, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)
pred = model.predict(X_test)

print("截距:", round(float(model.intercept_), 2))
print("前 5 个预测:", np.round(pred[:5], 1))
print("前 5 个真实:", y_test[:5])


pairs = sorted(
    zip(diabetes.feature_names, model.coef_),
    key=lambda item: abs(item[1]),
    reverse=True,
)
for name, coef in pairs:
    print(f"{name:>4}: {coef: .3f}")


from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

mae = mean_absolute_error(y_test, pred)
rmse = root_mean_squared_error(y_test, pred)
r2 = r2_score(y_test, pred)

print("MAE:", round(mae, 2))
print("RMSE:", round(rmse, 2))
print("R2:", round(r2, 3))


residual = y_test - pred

print("残差均值:", round(float(residual.mean()), 2))
print("残差标准差:", round(float(residual.std()), 2))
print("残差与预测值的相关系数:", round(float(np.corrcoef(residual, pred)[0, 1]), 3))
print("正残差个数:", int((residual > 0).sum()))
print("负残差个数:", int((residual < 0).sum()))

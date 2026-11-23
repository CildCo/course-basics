import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

diabetes = load_diabetes()
X_train, X_test, y_train, y_test = train_test_split(
    diabetes.data, diabetes.target, test_size=0.2, random_state=42
)

for degree in [1, 2, 3]:
    model = make_pipeline(
        PolynomialFeatures(degree=degree, include_bias=False),
        LinearRegression(),
    )
    model.fit(X_train, y_train)
    train_r2 = r2_score(y_train, model.predict(X_train))
    test_r2 = r2_score(y_test, model.predict(X_test))
    n_features = model.named_steps["polynomialfeatures"].n_output_features_
    print(
        f"degree={degree} 特征数={n_features} "
        f"训练 R2={train_r2:.3f} 测试 R2={test_r2:.3f}"
    )


from sklearn.linear_model import Ridge

for alpha in [0.01, 0.1, 1, 10, 100]:
    model = make_pipeline(
        PolynomialFeatures(degree=2, include_bias=False),
        Ridge(alpha=alpha),
    )
    model.fit(X_train, y_train)
    train_r2 = r2_score(y_train, model.predict(X_train))
    test_r2 = r2_score(y_test, model.predict(X_test))
    print(f"alpha={alpha:<6} 训练 R2={train_r2:.3f} 测试 R2={test_r2:.3f}")


from sklearn.linear_model import Lasso

for alpha in [0.01, 0.1, 1, 10]:
    model = make_pipeline(
        PolynomialFeatures(degree=2, include_bias=False),
        Lasso(alpha=alpha, max_iter=20000),
    )
    model.fit(X_train, y_train)
    coef = model.named_steps["lasso"].coef_
    train_r2 = r2_score(y_train, model.predict(X_train))
    test_r2 = r2_score(y_test, model.predict(X_test))
    print(
        f"alpha={alpha:<5} 非零系数={int((coef != 0).sum()):>3} "
        f"训练 R2={train_r2:.3f} 测试 R2={test_r2:.3f}"
    )

import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes

diabetes = load_diabetes()
df = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
df["age_group"] = pd.qcut(
    df["age"], q=3, labels=["young", "middle", "old"]
).astype(str)
y = diabetes.target

print(df.head(3).round(3).to_string())
print("\n列类型:")
print(df.dtypes.to_string())


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

X_train, X_test, y_train, y_test = train_test_split(
    df, y, test_size=0.2, random_state=42
)

numeric_cols = [c for c in df.columns if c != "age_group"]
preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["age_group"]),
    ]
)

X_train_t = preprocess.fit_transform(X_train)
X_test_t = preprocess.transform(X_test)

print("训练集转换后:", X_train_t.shape)
print("测试集转换后:", X_test_t.shape)
print("第一行前 5 个值:", np.round(X_train_t[0, :5], 3))


scaler_all = StandardScaler().fit(df[numeric_cols])
scaler_train = StandardScaler().fit(X_train[numeric_cols])

print("全量拟合的 age 均值:", round(float(scaler_all.mean_[0]), 6))
print("训练集拟合的 age 均值:", round(float(scaler_train.mean_[0]), 6))
print("两者差异:", round(abs(float(scaler_all.mean_[0] - scaler_train.mean_[0])), 6))
print(
    "用全量 scaler 转换测试集后的均值:",
    round(float(scaler_all.transform(X_test[numeric_cols])[:, 0].mean()), 4),
)


names = preprocess.get_feature_names_out()
print("转换后特征数:", len(names))
print("前 5 个:", list(names[:5]))
print("最后 3 个:", list(names[-3:]))

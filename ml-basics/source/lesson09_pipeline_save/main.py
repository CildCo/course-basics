import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

diabetes = load_diabetes()
df = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
df["age_group"] = pd.qcut(
    df["age"], q=3, labels=["young", "middle", "old"]
).astype(str)
y = diabetes.target

X_train, X_test, y_train, y_test = train_test_split(
    df, y, test_size=0.2, random_state=42
)
print("训练集:", X_train.shape, "测试集:", X_test.shape)


numeric_cols = [c for c in df.columns if c != "age_group"]
preprocess = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["age_group"]),
    ]
)
pipeline = Pipeline([
    ("prep", preprocess),
    ("model", LinearRegression()),
])
pipeline.fit(X_train, y_train)

print(pipeline)
print("测试集 R2:", round(r2_score(y_test, pipeline.predict(X_test)), 3))


output_dir = Path.cwd() / "output"
output_dir.mkdir(exist_ok=True)
model_path = output_dir / "diabetes_pipeline.joblib"

joblib.dump(pipeline, model_path)
print("保存路径:", model_path.relative_to(Path.cwd()).as_posix())
print("文件大小:", model_path.stat().st_size, "字节")


loaded = joblib.load(model_path)
new_row = X_test.iloc[[0]].copy()

print("新样本:")
print(new_row.to_string(index=False))
print("预测值:", round(float(loaded.predict(new_row)[0]), 2))
print("真实值:", round(float(y_test[0]), 2))

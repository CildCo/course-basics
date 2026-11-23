import pandas as pd

scores = pd.Series([88, 95, 79], index=["语文", "数学", "英语"], name="分数")
scores


df = pd.DataFrame({
    "科目": ["语文", "数学", "英语"],
    "分数": [88, 95, 79],
})
df


print(df.shape)
print(df.columns.tolist())
print(df.dtypes)


df.head(2)

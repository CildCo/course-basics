import pandas as pd

sales = pd.DataFrame({
    "category": ["办公", "数码", "家居", "办公"],
    "amount": [1200, 980, 450, 760],
})
targets = pd.DataFrame({
    "category": ["办公", "数码", "家居"],
    "target": [2000, 1500, 800],
})
print(sales.shape, targets.shape)


merged = sales.merge(targets, on="category", how="left")
merged


merged = merged.assign(rate=(merged["amount"] / merged["target"]).round(2))
merged

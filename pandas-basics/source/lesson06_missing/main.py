import pandas as pd

data = pd.DataFrame({
    "product": ["A", "B", "C", "D"],
    "units": [10, None, 5, 8],
    "price": [9.9, 12.0, None, 15.0],
})
data


data.isna().sum()


filled = data.fillna({"units": 0, "price": data["price"].mean()})
filled


print(data.dropna().shape)
print(data.dropna(subset=["price"]).shape)

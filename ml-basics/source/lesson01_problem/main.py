from sklearn.datasets import load_iris
import numpy as np

iris = load_iris()
X = iris.data
y = iris.target

print("特征矩阵 X:", X.shape)
print("标签向量 y:", y.shape)
print("特征名:", iris.feature_names)
print("类别名:", iris.target_names)
print("前 3 行特征:")
print(np.round(X[:3], 2))
print("标签分布:", np.bincount(y))


from sklearn.neighbors import KNeighborsClassifier

model = KNeighborsClassifier(n_neighbors=3)
model.fit(X, y)

samples = np.array([
    [5.1, 3.5, 1.4, 0.2],
    [6.7, 3.0, 5.2, 2.3],
])
pred = model.predict(samples)
proba = model.predict_proba(samples)

for row, idx, probs in zip(samples, pred, proba):
    print("样本", row, "->", iris.target_names[idx], "概率:", np.round(probs, 2))


from sklearn.cluster import KMeans

km = KMeans(n_clusters=3, n_init=10, random_state=42)
clusters = km.fit_predict(X)

print("每个簇的样本数:", np.bincount(clusters))
print("前 10 个样本的簇编号:", clusters[:10])

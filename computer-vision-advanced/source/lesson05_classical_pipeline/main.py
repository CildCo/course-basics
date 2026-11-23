import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import Image, display


def data_path(name):
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


output = Path("output")
output.mkdir(exist_ok=True)
print("输出目录已就绪")

from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

digits = load_digits()
images = np.stack([
    cv2.resize(image.astype(np.uint8), (16, 16), interpolation=cv2.INTER_CUBIC)
    for image in digits.images
]).astype(np.float32) / 255.0
labels = digits.target

X_train, X_test, y_train, y_test = train_test_split(
    images, labels, test_size=0.25, random_state=42, stratify=labels
)
print("图像批形状：", images.shape)
print("像素范围：", round(float(images.min()), 3), "到", round(float(images.max()), 3))
print("训练集 / 测试集：", X_train.shape[0], X_test.shape[0])
print("训练集每类数量：", np.bincount(y_train, minlength=10).tolist())


fig, axes = plt.subplots(2, 5, figsize=(9, 3.8))
for digit, ax in enumerate(axes.ravel()):
    index = np.where(y_train == digit)[0][0]
    ax.imshow(X_train[index], cmap="gray")
    ax.set_title(f"标签 {digit}")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "samples16.png", dpi=110)
display(Image(filename=str(output / "samples16.png")))
plt.close(fig)


def hog_features(image, cell=4, bins=9):
    gx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
    magnitude, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    angle = angle % 180
    height, width = image.shape
    cells_y, cells_x = height // cell, width // cell
    bin_width = 180 / bins
    features = []
    for row in range(cells_y):
        for col in range(cells_x):
            block = np.s_[row * cell:(row + 1) * cell, col * cell:(col + 1) * cell]
            weights = magnitude[block].ravel()
            directions = np.clip(
                (angle[block].ravel() / bin_width).astype(int), 0, bins - 1
            )
            histogram = np.bincount(
                directions, weights=weights, minlength=bins
            ).astype(np.float32)
            histogram /= np.linalg.norm(histogram) + 1e-6
            features.append(histogram)
    return np.concatenate(features)


sample_features = hog_features(X_train[0])
print("单张图的 HOG 维度：", sample_features.shape[0])
print("前 9 个值：", sample_features[:9].round(3).tolist())

fig, axes = plt.subplots(1, 3, figsize=(10, 3.4))
for ax, index in zip(axes, [0, 1, 2]):
    descriptor = hog_features(X_train[index]).reshape(16, 9)
    ax.imshow(descriptor, cmap="magma", aspect="auto")
    ax.set_title(f"标签 {y_train[index]} 的 HOG")
    ax.set_xlabel("方向 bin")
    ax.set_ylabel("单元")
fig.tight_layout()
fig.savefig(output / "hog.png", dpi=110)
display(Image(filename=str(output / "hog.png")))
plt.close(fig)


from sklearn.decomposition import PCA
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

hog_train = np.stack([hog_features(image) for image in X_train])
hog_test = np.stack([hog_features(image) for image in X_test])
raw_train = X_train.reshape(len(X_train), -1)
raw_test = X_test.reshape(len(X_test), -1)
print("HOG 特征矩阵：", hog_train.shape, hog_test.shape)
print("原始像素矩阵：", raw_train.shape, raw_test.shape)


def make_pipeline():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=40, random_state=42)),
        ("svm", SVC(kernel="rbf", C=10, gamma="scale")),
    ])


hog_scores = cross_val_score(make_pipeline(), hog_train, y_train, cv=5)
hog_model = make_pipeline().fit(hog_train, y_train)
hog_test_acc = hog_model.score(hog_test, y_test)
print("HOG 五折分数：", hog_scores.round(4).tolist())
print("HOG 平均分：", round(float(hog_scores.mean()), 4), "+-", round(float(hog_scores.std()), 4))
print("HOG 测试集准确率：", round(float(hog_test_acc), 4))


raw_scores = cross_val_score(make_pipeline(), raw_train, y_train, cv=5)
raw_model = make_pipeline().fit(raw_train, y_train)
raw_test_acc = raw_model.score(raw_test, y_test)
print("原始像素五折分数：", raw_scores.round(4).tolist())
print("原始像素平均分：", round(float(raw_scores.mean()), 4), "+-", round(float(raw_scores.std()), 4))
print("原始像素测试集准确率：", round(float(raw_test_acc), 4))

fig, ax = plt.subplots(figsize=(6.4, 3.6))
positions = np.arange(2)
cv_means = [raw_scores.mean(), hog_scores.mean()]
cv_stds = [raw_scores.std(), hog_scores.std()]
test_scores = [raw_test_acc, hog_test_acc]
ax.bar(positions - 0.18, cv_means, width=0.36, yerr=cv_stds, capsize=4, label="五折平均")
ax.bar(positions + 0.18, test_scores, width=0.36, label="测试集")
ax.set_xticks(positions)
ax.set_xticklabels(["原始像素", "HOG"])
ax.set_ylim(0.9, 1.0)
ax.set_ylabel("准确率")
ax.set_title("两种特征方案的准确率")
ax.legend()
fig.tight_layout()
fig.savefig(output / "comparison.png", dpi=110)
display(Image(filename=str(output / "comparison.png")))
plt.close(fig)

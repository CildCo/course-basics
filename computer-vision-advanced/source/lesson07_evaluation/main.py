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
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import SVC

digits = load_digits()
images = np.stack([
    cv2.resize(image.astype(np.uint8), (16, 16), interpolation=cv2.INTER_CUBIC)
    for image in digits.images
]).astype(np.float32) / 255.0
labels = digits.target


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


X_train, X_test, y_train, y_test = train_test_split(
    images, labels, test_size=0.25, random_state=42, stratify=labels
)
hog_train = np.stack([hog_features(image) for image in X_train])
hog_test = np.stack([hog_features(image) for image in X_test])

model = Pipeline([
    ("scaler", StandardScaler()),
    ("pca", PCA(n_components=40, random_state=42)),
    ("svm", SVC(kernel="rbf", C=10, gamma="scale")),
]).fit(hog_train, y_train)
predictions = model.predict(hog_test)
accuracy = float((predictions == y_test).mean())
print("测试集样本数：", len(y_test))
print("测试集准确率：", round(accuracy, 4))


matrix = confusion_matrix(y_test, predictions)
print("混淆矩阵（行=真实，列=预测）：")
print(matrix)

fig, ax = plt.subplots(figsize=(6.6, 5.6))
image = ax.imshow(matrix, cmap="Blues")
for row in range(matrix.shape[0]):
    for col in range(matrix.shape[1]):
        value = matrix[row, col]
        color = "white" if value > matrix.max() / 2 else "black"
        ax.text(col, row, str(value), ha="center", va="center", color=color, fontsize=9)
ax.set_xlabel("预测类别")
ax.set_ylabel("真实类别")
ax.set_xticks(range(10))
ax.set_yticks(range(10))
ax.set_title("测试集混淆矩阵")
fig.colorbar(image, ax=ax, shrink=0.8)
fig.tight_layout()
fig.savefig(output / "confusion_matrix.png", dpi=110)
display(Image(filename=str(output / "confusion_matrix.png")))
plt.close(fig)


report = classification_report(y_test, predictions, zero_division=0, output_dict=True)
print(classification_report(y_test, predictions, zero_division=0))
print("macro F1：", round(report["macro avg"]["f1-score"], 4))
print("weighted F1：", round(report["weighted avg"]["f1-score"], 4))

per_class_f1 = [report[str(digit)]["f1-score"] for digit in range(10)]
per_class_recall = [report[str(digit)]["recall"] for digit in range(10)]
fig, ax = plt.subplots(figsize=(8, 3.6))
positions = np.arange(10)
ax.bar(positions - 0.2, per_class_recall, width=0.4, label="召回率")
ax.bar(positions + 0.2, per_class_f1, width=0.4, label="F1")
ax.set_xticks(positions)
ax.set_xlabel("数字类别")
ax.set_ylim(0.85, 1.02)
ax.set_title("每个类别的召回率和 F1")
ax.legend()
fig.tight_layout()
fig.savefig(output / "per_class_f1.png", dpi=110)
display(Image(filename=str(output / "per_class_f1.png")))
plt.close(fig)


wrong_indices = np.where(predictions != y_test)[0]
print("错误样本数：", len(wrong_indices))

pairs = {}
for index in wrong_indices:
    key = (int(y_test[index]), int(predictions[index]))
    pairs[key] = pairs.get(key, 0) + 1
ranked = sorted(pairs.items(), key=lambda item: (-item[1], item[0]))
print("错误组合（真实 -> 预测）：")
for (true_label, predicted_label), count in ranked:
    print(f"  {true_label} -> {predicted_label}：{count} 张")

fig, axes = plt.subplots(2, 4, figsize=(9, 4.8))
for ax, index in zip(axes.ravel(), wrong_indices[:8]):
    ax.imshow(X_test[index], cmap="gray")
    ax.set_title(
        f"真 {y_test[index]} -> 预 {predictions[index]}",
        color="crimson",
        fontsize=9,
    )
    ax.axis("off")
for ax in axes.ravel()[len(wrong_indices[:8]):]:
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "errors.png", dpi=110)
display(Image(filename=str(output / "errors.png")))
plt.close(fig)

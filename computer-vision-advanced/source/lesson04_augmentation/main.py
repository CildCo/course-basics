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
images = digits.images
labels = digits.target
print("图像批形状：", images.shape)
print("标签形状：", labels.shape)
print("像素范围：", int(images.min()), "到", int(images.max()))
print("类别：", sorted(set(labels.tolist())))
print("每类样本数：", np.bincount(labels).tolist())


fig, axes = plt.subplots(2, 5, figsize=(9, 3.8))
for digit, ax in enumerate(axes.ravel()):
    index = np.where(labels == digit)[0][0]
    ax.imshow(images[index], cmap="gray")
    ax.set_title(f"数字 {digit}")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "samples.png", dpi=110)
display(Image(filename=str(output / "samples.png")))
plt.close(fig)


from PIL import Image as PILImage

shape = np.array(PILImage.open(data_path("images/shapes.png")).convert("L"))


def rotate(image, angle):
    height, width = image.shape
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (width, height), flags=cv2.INTER_LINEAR, borderValue=255)


def change_brightness(image, factor):
    return np.clip(image.astype(np.float32) * factor, 0, 255).astype(np.uint8)


variants = [
    ("原图", shape),
    ("水平翻转", np.ascontiguousarray(shape[:, ::-1])),
    ("旋转 12 度", rotate(shape, 12)),
    ("旋转 -12 度", rotate(shape, -12)),
    ("亮度 0.7", change_brightness(shape, 0.7)),
    ("亮度 1.3", change_brightness(shape, 1.3)),
]
fig, axes = plt.subplots(2, 3, figsize=(10, 6))
for ax, (name, picture) in zip(axes.ravel(), variants):
    ax.imshow(picture, cmap="gray", vmin=0, vmax=255)
    ax.set_title(name)
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "shape_augment.png", dpi=110)
display(Image(filename=str(output / "shape_augment.png")))
plt.close(fig)
print("形状增强示例：", len(variants), "种")


X_train, X_test, y_train, y_test = train_test_split(
    images, labels, test_size=0.25, random_state=42, stratify=labels
)


def augment_digit(image, rng):
    uint8 = (image / 16 * 255).astype(np.uint8)
    height, width = uint8.shape
    angle = rng.uniform(-12, 12)
    scale = rng.uniform(0.9, 1.1)
    matrix = cv2.getRotationMatrix2D((width / 2 - 0.5, height / 2 - 0.5), angle, scale)
    matrix[0, 2] += rng.uniform(-1.2, 1.2)
    matrix[1, 2] += rng.uniform(-1.2, 1.2)
    moved = cv2.warpAffine(uint8, matrix, (width, height), flags=cv2.INTER_LINEAR, borderValue=0)
    factor = rng.uniform(0.85, 1.15)
    moved = np.clip(moved.astype(np.float32) * factor, 0, 255)
    return moved / 255 * 16


rng = np.random.RandomState(42)
X_augmented = [X_train]
y_augmented = [y_train]
for _ in range(2):
    X_augmented.append(np.stack([augment_digit(image, rng) for image in X_train]))
    y_augmented.append(y_train)

X_train_aug = np.concatenate(X_augmented)
y_train_aug = np.concatenate(y_augmented)
print("原始训练集：", X_train.shape)
print("增强后训练集：", X_train_aug.shape)
print("测试集保持不变：", X_test.shape)
print("增强后每类数量：", np.bincount(y_train_aug).tolist())

fig, axes = plt.subplots(2, 5, figsize=(9, 4))
axes[0, 0].imshow(X_train[0], cmap="gray")
axes[0, 0].set_title("原始")
axes[0, 0].axis("off")
for step, ax in enumerate(axes.ravel()[1:], start=1):
    ax.imshow(augment_digit(X_train[0], np.random.RandomState(step)), cmap="gray")
    ax.set_title(f"增强 {step}")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "digit_augment.png", dpi=110)
display(Image(filename=str(output / "digit_augment.png")))
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.6))
positions = np.arange(10)
ax.bar(positions - 0.2, np.bincount(y_train, minlength=10), width=0.4, label="原始")
ax.bar(positions + 0.2, np.bincount(y_train_aug, minlength=10), width=0.4, label="增强后")
ax.set_xticks(positions)
ax.set_xlabel("数字类别")
ax.set_ylabel("样本数")
ax.set_title("增强前后每类样本数")
ax.legend()
fig.tight_layout()
fig.savefig(output / "augment_counts.png", dpi=110)
display(Image(filename=str(output / "augment_counts.png")))
plt.close(fig)


train_mean = float(X_train_aug.mean())
train_std = float(X_train_aug.std())
all_mean = float(images.mean())

print("训练集均值 / 标准差：", round(train_mean, 3), round(train_std, 3))
print("全体数据均值（仅作对比）：", round(all_mean, 3))
print("两者差值：", round(abs(train_mean - all_mean), 4))

X_train_normalized = (X_train_aug - train_mean) / (train_std + 1e-6)
X_test_normalized = (X_test - train_mean) / (train_std + 1e-6)

print("归一化后训练集范围：", round(float(X_train_normalized.min()), 2), "到", round(float(X_train_normalized.max()), 2))
print("归一化后测试集范围：", round(float(X_test_normalized.min()), 2), "到", round(float(X_test_normalized.max()), 2))
print("训练集归一化后均值：", round(float(X_train_normalized.mean()), 6))

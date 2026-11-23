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

import json
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

torch.manual_seed(42)
np.random.seed(42)

IMAGE_SIZE = 16
BATCH_SIZE = 64
EPOCHS = 8

digits = load_digits()
images = np.stack([
    cv2.resize(image.astype(np.uint8), (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_CUBIC)
    for image in digits.images
]).astype(np.float32) / 255.0
labels = digits.target

X_train, X_rest, y_train, y_rest = train_test_split(
    images, labels, test_size=0.4, random_state=42, stratify=labels
)
X_val, X_test, y_val, y_test = train_test_split(
    X_rest, y_rest, test_size=0.5, random_state=42, stratify=y_rest
)
print("训练 / 验证 / 测试：", len(X_train), len(X_val), len(X_test))
print("训练集每类数量：", np.bincount(y_train, minlength=10).tolist())
print("验证集每类数量：", np.bincount(y_val, minlength=10).tolist())
print("测试集每类数量：", np.bincount(y_test, minlength=10).tolist())


fig, axes = plt.subplots(2, 5, figsize=(9, 3.8))
for digit, ax in enumerate(axes.ravel()):
    index = np.where(y_test == digit)[0][0]
    ax.imshow(X_test[index], cmap="gray")
    ax.set_title(f"测试样本 {digit}")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "project_samples.png", dpi=110)
display(Image(filename=str(output / "project_samples.png")))
plt.close(fig)


def augment(image, rng):
    uint8 = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    height, width = uint8.shape
    angle = rng.uniform(-12, 12)
    scale = rng.uniform(0.9, 1.1)
    matrix = cv2.getRotationMatrix2D((width / 2 - 0.5, height / 2 - 0.5), angle, scale)
    matrix[0, 2] += rng.uniform(-1.2, 1.2)
    matrix[1, 2] += rng.uniform(-1.2, 1.2)
    moved = cv2.warpAffine(
        uint8, matrix, (width, height), flags=cv2.INTER_LINEAR, borderValue=0
    )
    factor = rng.uniform(0.85, 1.15)
    return np.clip(moved.astype(np.float32) * factor, 0, 255) / 255


rng = np.random.RandomState(42)
X_train_augmented = [X_train]
y_train_augmented = [y_train]
for _ in range(2):
    X_train_augmented.append(np.stack([augment(image, rng) for image in X_train]))
    y_train_augmented.append(y_train)
X_train_augmented = np.concatenate(X_train_augmented)
y_train_augmented = np.concatenate(y_train_augmented)

print("增强前训练集：", X_train.shape)
print("增强后训练集：", X_train_augmented.shape)
print("增强后每类数量：", np.bincount(y_train_augmented, minlength=10).tolist())

fig, axes = plt.subplots(1, 9, figsize=(12, 2.2))
axes[0].imshow(X_train[0], cmap="gray")
axes[0].set_title("原始", fontsize=9)
axes[0].axis("off")
for step, ax in enumerate(axes[1:], start=1):
    ax.imshow(augment(X_train[0], np.random.RandomState(step)), cmap="gray")
    ax.set_title(f"增强 {step}", fontsize=9)
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "augmented_examples.png", dpi=110)
display(Image(filename=str(output / "augmented_examples.png")))
plt.close(fig)


train_mean = float(X_train_augmented.mean())
train_std = float(X_train_augmented.std())
X_train_norm = (X_train_augmented - train_mean) / (train_std + 1e-6)
X_val_norm = (X_val - train_mean) / (train_std + 1e-6)
X_test_norm = (X_test - train_mean) / (train_std + 1e-6)
print("归一化参数：均值", round(train_mean, 4), "标准差", round(train_std, 4))

train_dataset = TensorDataset(
    torch.tensor(X_train_norm).unsqueeze(1),
    torch.tensor(y_train_augmented, dtype=torch.long),
)
val_dataset = TensorDataset(
    torch.tensor(X_val_norm).unsqueeze(1),
    torch.tensor(y_val, dtype=torch.long),
)
test_dataset = TensorDataset(
    torch.tensor(X_test_norm).unsqueeze(1),
    torch.tensor(y_test, dtype=torch.long),
)
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=128, shuffle=False)
print("训练批次数：", len(train_loader))
print("验证 / 测试样本数：", len(val_dataset), len(test_dataset))


class DigitCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 4 * 4, 64),
            nn.ReLU(),
            nn.Linear(64, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def evaluate(model, loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_inputs, batch_targets in loader:
            outputs = model(batch_inputs)
            correct += (outputs.argmax(1) == batch_targets).sum().item()
            total += len(batch_targets)
    return correct / total


model = DigitCNN()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
best_val_accuracy = 0.0
best_state = {key: value.clone() for key, value in model.state_dict().items()}
history = {"train_loss": [], "train_acc": [], "val_acc": []}
start = time.time()

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    for batch_inputs, batch_targets in train_loader:
        optimizer.zero_grad()
        outputs = model(batch_inputs)
        loss = criterion(outputs, batch_targets)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(batch_targets)
        correct += (outputs.argmax(1) == batch_targets).sum().item()
        total += len(batch_targets)

    train_loss = total_loss / total
    train_accuracy = correct / total
    val_accuracy = evaluate(model, val_loader)
    history["train_loss"].append(train_loss)
    history["train_acc"].append(train_accuracy)
    history["val_acc"].append(val_accuracy)
    if val_accuracy > best_val_accuracy:
        best_val_accuracy = val_accuracy
        best_state = {key: value.clone() for key, value in model.state_dict().items()}
    print(
        f"第 {epoch + 1} 轮  损失 {train_loss:.4f}  "
        f"训练准确率 {train_accuracy:.4f}  验证准确率 {val_accuracy:.4f}"
    )

model.load_state_dict(best_state)
print("最佳验证准确率：", round(best_val_accuracy, 4))
print("训练用时：", round(time.time() - start, 2), "秒")

epochs = np.arange(1, len(history["train_loss"]) + 1)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
axes[0].plot(epochs, history["train_loss"], marker="o", color="#3b6ea5")
axes[0].set_title("训练损失")
axes[0].set_xlabel("轮次")
axes[0].set_ylabel("交叉熵")
axes[1].plot(epochs, history["train_acc"], marker="o", label="训练")
axes[1].plot(epochs, history["val_acc"], marker="o", label="验证")
axes[1].set_title("准确率")
axes[1].set_xlabel("轮次")
axes[1].set_ylim(0.5, 1.02)
axes[1].legend()
fig.tight_layout()
fig.savefig(output / "project_curves.png", dpi=110)
display(Image(filename=str(output / "project_curves.png")))
plt.close(fig)


model.eval()
with torch.no_grad():
    logits = model(torch.tensor(X_test_norm).unsqueeze(1))
    predictions = logits.argmax(1).numpy()
    probabilities = torch.softmax(logits, dim=1)

test_accuracy = accuracy_score(y_test, predictions)
print("测试集准确率：", round(float(test_accuracy), 4))
print(classification_report(y_test, predictions, zero_division=0))

matrix = confusion_matrix(y_test, predictions)
fig, ax = plt.subplots(figsize=(6.6, 5.6))
image = ax.imshow(matrix, cmap="Greens")
for row in range(matrix.shape[0]):
    for col in range(matrix.shape[1]):
        value = matrix[row, col]
        color = "white" if value > matrix.max() / 2 else "black"
        ax.text(col, row, str(value), ha="center", va="center", color=color, fontsize=9)
ax.set_xlabel("预测类别")
ax.set_ylabel("真实类别")
ax.set_xticks(range(10))
ax.set_yticks(range(10))
ax.set_title("项目测试集混淆矩阵")
fig.colorbar(image, ax=ax, shrink=0.8)
fig.tight_layout()
fig.savefig(output / "project_confusion.png", dpi=110)
display(Image(filename=str(output / "project_confusion.png")))
plt.close(fig)


model_path = output / "digit_cnn.pt"
torch.save(
    {
        "state_dict": model.state_dict(),
        "image_size": IMAGE_SIZE,
        "mean": train_mean,
        "std": train_std,
        "classes": list(range(10)),
    },
    model_path,
)

metrics = {
    "accuracy": round(float(test_accuracy), 4),
    "imageSize": IMAGE_SIZE,
    "epochs": EPOCHS,
    "samples": {
        "train": int(len(X_train_augmented)),
        "val": int(len(X_val)),
        "test": int(len(X_test)),
    },
    "bestValAccuracy": round(float(best_val_accuracy), 4),
}
metrics_path = output / "metrics.json"
metrics_path.write_text(
    json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("模型文件：", model_path.name, model_path.stat().st_size, "字节")
print("指标文件：", metrics_path.name, metrics_path.stat().st_size, "字节")
print(json.dumps(metrics, ensure_ascii=False, indent=2))

checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
restored = DigitCNN()
restored.load_state_dict(checkpoint["state_dict"])
restored.eval()
with torch.no_grad():
    sample_logits = restored(torch.tensor(X_test_norm[:5]).unsqueeze(1))
    sample_pred = sample_logits.argmax(1).numpy()
print("重新加载后的预测：", sample_pred.tolist())
print("真实标签：", y_test[:5].tolist())


def make_variant(image, angle, noise, rng):
    uint8 = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    height, width = uint8.shape
    matrix = cv2.getRotationMatrix2D((width / 2 - 0.5, height / 2 - 0.5), angle, 1.0)
    moved = cv2.warpAffine(
        uint8, matrix, (width, height), flags=cv2.INTER_LINEAR, borderValue=0
    )
    noisy = moved.astype(np.float32) + rng.normal(0, noise, moved.shape).astype(np.float32)
    return (np.clip(noisy, 0, 255) / 255).astype(np.float32)


variant_rng = np.random.RandomState(9)
indices = variant_rng.choice(len(X_test), 6, replace=False)
variants = []
for index in indices:
    angle = variant_rng.uniform(-15, 15)
    variants.append(make_variant(X_test[index], angle, 12, variant_rng))
variants = np.stack(variants)
variants_norm = (variants - train_mean) / (train_std + 1e-6)

with torch.no_grad():
    variant_logits = restored(torch.tensor(variants_norm).unsqueeze(1))
    variant_pred = variant_logits.argmax(1).numpy()
    variant_conf = torch.softmax(variant_logits, dim=1).max(1).values.numpy()

fig, axes = plt.subplots(2, 3, figsize=(9, 4.8))
for ax, index, picture, predicted, confidence in zip(
    axes.ravel(), indices, variants, variant_pred, variant_conf
):
    ax.imshow(picture, cmap="gray")
    ok = predicted == y_test[index]
    ax.set_title(
        f"真 {y_test[index]} / 预 {predicted}\n置信度 {confidence:.0%}",
        color="green" if ok else "crimson",
        fontsize=9,
    )
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "project_inference.png", dpi=110)
display(Image(filename=str(output / "project_inference.png")))
plt.close(fig)

print("干扰样本预测：", variant_pred.tolist())
print("干扰样本真实：", y_test[indices].tolist())
print("干扰样本正确数：", int((variant_pred == y_test[indices]).sum()), "/", len(indices))

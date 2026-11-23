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

import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

torch.manual_seed(42)
np.random.seed(42)

digits = load_digits()
images = np.stack([
    cv2.resize(image.astype(np.uint8), (16, 16), interpolation=cv2.INTER_CUBIC)
    for image in digits.images
]).astype(np.float32) / 255.0
labels = digits.target

X_train, X_test, y_train, y_test = train_test_split(
    images, labels, test_size=0.25, random_state=42, stratify=labels
)
train_mean = float(X_train.mean())
train_std = float(X_train.std())
X_train = (X_train - train_mean) / (train_std + 1e-6)
X_test = (X_test - train_mean) / (train_std + 1e-6)

print("训练集 / 测试集：", X_train.shape, X_test.shape)
print("训练集均值 / 标准差：", round(train_mean, 3), round(train_std, 3))
print("归一化后范围：", round(float(X_train.min()), 2), "到", round(float(X_train.max()), 2))


fig, axes = plt.subplots(2, 5, figsize=(9, 3.8))
for digit, ax in enumerate(axes.ravel()):
    index = np.where(y_train == digit)[0][0]
    ax.imshow(X_train[index] * train_std + train_mean, cmap="gray")
    ax.set_title(f"标签 {digit}")
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "cnn_samples.png", dpi=110)
display(Image(filename=str(output / "cnn_samples.png")))
plt.close(fig)

train_dataset = TensorDataset(
    torch.tensor(X_train).unsqueeze(1),
    torch.tensor(y_train, dtype=torch.long),
)
test_dataset = TensorDataset(
    torch.tensor(X_test).unsqueeze(1),
    torch.tensor(y_test, dtype=torch.long),
)
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=128, shuffle=False)

inputs, targets = next(iter(train_loader))
print("一个批次图像：", tuple(inputs.shape))
print("一个批次标签：", tuple(targets.shape))
print("训练批次数：", len(train_loader))


class SmallCNN(nn.Module):
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


model = SmallCNN()
print(model)
print("参数量：", sum(parameter.numel() for parameter in model.parameters()))
with torch.no_grad():
    print("输出形状：", tuple(model(inputs).shape))


criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
history = {"loss": [], "train_acc": [], "test_acc": []}
start = time.time()

for epoch in range(6):
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

    model.eval()
    test_correct = 0
    test_total = 0
    with torch.no_grad():
        for batch_inputs, batch_targets in test_loader:
            outputs = model(batch_inputs)
            test_correct += (outputs.argmax(1) == batch_targets).sum().item()
            test_total += len(batch_targets)

    history["loss"].append(total_loss / total)
    history["train_acc"].append(correct / total)
    history["test_acc"].append(test_correct / test_total)
    print(
        f"第 {epoch + 1} 轮  损失 {history['loss'][-1]:.4f}  "
        f"训练准确率 {history['train_acc'][-1]:.4f}  "
        f"测试准确率 {history['test_acc'][-1]:.4f}"
    )

print("训练用时：", round(time.time() - start, 2), "秒")

epochs = np.arange(1, len(history["loss"]) + 1)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
axes[0].plot(epochs, history["loss"], marker="o", color="#3b6ea5")
axes[0].set_title("训练损失")
axes[0].set_xlabel("轮次")
axes[0].set_ylabel("交叉熵")
axes[1].plot(epochs, history["train_acc"], marker="o", label="训练")
axes[1].plot(epochs, history["test_acc"], marker="o", label="测试")
axes[1].set_title("准确率")
axes[1].set_xlabel("轮次")
axes[1].set_ylim(0.5, 1.02)
axes[1].legend()
fig.tight_layout()
fig.savefig(output / "training_curves.png", dpi=110)
display(Image(filename=str(output / "training_curves.png")))
plt.close(fig)


model.eval()
with torch.no_grad():
    logits = model(torch.tensor(X_test).unsqueeze(1))
    probabilities = torch.softmax(logits, dim=1)
    predictions = logits.argmax(1).numpy()
    confidences = probabilities.max(1).values.numpy()

accuracy = float((predictions == y_test).mean())
print("测试集准确率：", round(accuracy, 4))
print("错误样本数：", int((predictions != y_test).sum()))

fig, axes = plt.subplots(2, 5, figsize=(9, 4.2))
indices = np.random.RandomState(3).choice(len(X_test), 10, replace=False)
for ax, index in zip(axes.ravel(), indices):
    ax.imshow(X_test[index] * train_std + train_mean, cmap="gray")
    ok = predictions[index] == y_test[index]
    ax.set_title(
        f"真 {y_test[index]} / 预 {predictions[index]}\n{confidences[index]:.0%}",
        color="green" if ok else "crimson",
        fontsize=9,
    )
    ax.axis("off")
fig.tight_layout()
fig.savefig(output / "predictions.png", dpi=110)
display(Image(filename=str(output / "predictions.png")))
plt.close(fig)

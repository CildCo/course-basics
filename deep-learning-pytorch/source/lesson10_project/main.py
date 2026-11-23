from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

import torch

torch.manual_seed(42)


def data_path(name):
    """课程素材统一放在 assets/，从当前目录向上查找。"""
    here = Path.cwd()
    for base in [here, here.parent, here.parent.parent]:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"没有找到素材：{name}")


out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

import hashlib
import json

import numpy as np
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from torch import nn
import torch.nn.functional as F

print("PyTorch:", torch.__version__)
print("输出目录:", out)


digits = load_digits()
X = digits.data.astype("float32")
y = digits.target.astype("int64")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

mean = X_train.mean(axis=0)
std = X_train.std(axis=0) + 1e-6
X_train_t = torch.from_numpy((X_train - mean) / std)
X_test_t = torch.from_numpy((X_test - mean) / std)
y_train_t = torch.from_numpy(y_train)
y_test_t = torch.from_numpy(y_test)

print("总样本:", len(X))
print("训练集:", X_train_t.shape, "测试集:", X_test_t.shape)
print("类别:", digits.target_names.tolist())
print("训练集类别分布:", np.bincount(y_train).tolist())


class DigitNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 10),
        )

    def forward(self, x):
        return self.net(x)


torch.manual_seed(42)
model = DigitNet()
print(model)
print("参数量:", sum(p.numel() for p in model.parameters()))


optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
history = {"loss": [], "train_acc": [], "test_acc": []}

for epoch in range(1, 13):
    model.train()
    perm = torch.randperm(len(X_train_t))
    epoch_loss = 0.0
    for start in range(0, len(perm), 32):
        idx = perm[start:start + 32]
        optimizer.zero_grad()
        loss = F.cross_entropy(model(X_train_t[idx]), y_train_t[idx])
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item() * len(idx)

    model.eval()
    with torch.no_grad():
        train_pred = model(X_train_t).argmax(dim=1)
        test_pred = model(X_test_t).argmax(dim=1)
        train_acc = (train_pred == y_train_t).float().mean().item()
        test_acc = (test_pred == y_test_t).float().mean().item()

    history["loss"].append(epoch_loss / len(X_train_t))
    history["train_acc"].append(train_acc)
    history["test_acc"].append(test_acc)
    print(f"epoch {epoch:02d}  损失 {history['loss'][-1]:.3f}  "
          f"训练准确率 {train_acc:.3f}  测试准确率 {test_acc:.3f}")


model.eval()
with torch.no_grad():
    logits = model(X_test_t)
    probs = torch.softmax(logits, dim=1).numpy()
    pred = probs.argmax(axis=1)

accuracy = accuracy_score(y_test, pred)
print("测试准确率:", round(float(accuracy), 4))
print()
print(classification_report(y_test, pred, digits=3, zero_division=0))


from IPython.display import Image, display
import matplotlib.pyplot as plt

cm = confusion_matrix(y_test, pred)

fig, ax = plt.subplots(figsize=(6.6, 5.6))
image = ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(10))
ax.set_yticks(range(10))
ax.set_xlabel("预测类别")
ax.set_ylabel("真实类别")
ax.set_title("测试集混淆矩阵")
for i in range(10):
    for j in range(10):
        color = "white" if cm[i, j] > cm.max() / 2 else "#333333"
        ax.text(j, i, cm[i, j], ha="center", va="center", color=color, fontsize=8)

fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
fig.tight_layout()
fig.savefig(out / "confusion-matrix.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "confusion-matrix.png")))
plt.close(fig)


fig, axes = plt.subplots(2, 4, figsize=(9, 4.8))
for ax, image, true_label, pred_label, score in zip(
    axes.flat, X_test[:8], y_test[:8], pred[:8], probs.max(axis=1)[:8]
):
    ax.imshow(image.reshape(8, 8), cmap="gray")
    ok = true_label == pred_label
    ax.set_title(f"真 {true_label} / 预 {pred_label}\n{score:.2f}", fontsize=9,
                 color="#2A6F4E" if ok else "#B23A3A")
    ax.axis("off")
fig.tight_layout()
fig.savefig(out / "project-samples.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "project-samples.png")))
plt.close(fig)

wrong = np.where(pred != y_test)[0]
print("错误样本数:", len(wrong))
print("前 5 个错误位置:", wrong[:5].tolist())


model_path = out / "digit-project-v1.0.0.pt"
checkpoint = {
    "state_dict": model.state_dict(),
    "mean": mean.tolist(),
    "std": std.tolist(),
    "classes": [str(i) for i in range(10)],
    "version": "1.0.0",
    "test_accuracy": round(float(accuracy), 4),
    "input_shape": [64],
    "torch_version": str(torch.__version__),
}
torch.save(checkpoint, model_path)

meta = {key: value for key, value in checkpoint.items() if key != "state_dict"}
meta["sha256_16"] = hashlib.sha256(model_path.read_bytes()).hexdigest()[:16]
meta["confusion_matrix"] = cm.tolist()
(out / "digit-project-meta.json").write_text(
    json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("模型文件:", model_path.name, model_path.stat().st_size, "字节")
print("版本:", meta["version"])
print("测试准确率:", meta["test_accuracy"])
print("SHA256 前 16 位:", meta["sha256_16"])

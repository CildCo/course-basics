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

from IPython.display import Image, display
import matplotlib.pyplot as plt
import torch.nn.functional as F
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

print("PyTorch:", torch.__version__)
print("输出目录:", out)


digits = load_digits()
mask = (digits.target == 3) | (digits.target == 8)
X = digits.data[mask].astype("float32")
y = (digits.target[mask] == 8).astype("int64")

X_train, X_val, y_train, y_val = train_test_split(
    X, y, train_size=32, random_state=42, stratify=y
)

mean = X_train.mean(axis=0)
std = X_train.std(axis=0) + 1e-6
X_train_t = torch.from_numpy((X_train - mean) / std)
X_val_t = torch.from_numpy((X_val - mean) / std)
y_train_t = torch.from_numpy(y_train)
y_val_t = torch.from_numpy(y_val)

print("训练集:", X_train_t.shape, "验证集:", X_val_t.shape)
print("训练集类别:", torch.bincount(y_train_t).tolist())
print("验证集类别:", torch.bincount(y_val_t).tolist())


from torch import nn


def make_model(dropout=0.0):
    layers = [nn.Flatten(), nn.Linear(64, 128), nn.ReLU()]
    if dropout > 0:
        layers.append(nn.Dropout(dropout))
    layers.append(nn.Linear(128, 2))
    return nn.Sequential(*layers)


def random_shift(images, max_shift=1):
    shifted = []
    for image in images:
        dy = torch.randint(-max_shift, max_shift + 1, (1,)).item()
        dx = torch.randint(-max_shift, max_shift + 1, (1,)).item()
        moved = torch.roll(image.view(8, 8), shifts=(dy, dx), dims=(0, 1))
        shifted.append(moved.reshape(-1))
    return torch.stack(shifted)


def run_config(name, dropout=0.0, weight_decay=0.0, augment=False, epochs=60):
    torch.manual_seed(0)
    model = make_model(dropout)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=1e-3, weight_decay=weight_decay
    )
    history = {"train": [], "val": [], "loss": []}

    for epoch in range(epochs):
        model.train()
        batch = random_shift(X_train_t) if augment else X_train_t
        optimizer.zero_grad()
        loss = F.cross_entropy(model(batch), y_train_t)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            train_acc = (model(X_train_t).argmax(dim=1) == y_train_t).float().mean().item()
            val_acc = (model(X_val_t).argmax(dim=1) == y_val_t).float().mean().item()

        history["train"].append(train_acc)
        history["val"].append(val_acc)
        history["loss"].append(loss.item())

    return model, history


configs = [
    ("基线", {"dropout": 0.0, "weight_decay": 0.0, "augment": False}),
    ("Dropout 0.5", {"dropout": 0.5, "weight_decay": 0.0, "augment": False}),
    ("权重衰减", {"dropout": 0.0, "weight_decay": 1e-2, "augment": False}),
    ("数据增强", {"dropout": 0.0, "weight_decay": 0.0, "augment": True}),
]

results = {}
for name, kwargs in configs:
    model, history = run_config(name, **kwargs)
    results[name] = history
    print(f"{name:<12} 最终训练准确率 {history['train'][-1]:.3f}  "
          f"最终验证准确率 {history['val'][-1]:.3f}  "
          f"最佳验证准确率 {max(history['val']):.3f}")


fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True, sharey=True)
for ax, (name, _) in zip(axes.flat, configs):
    history = results[name]
    ax.plot(history["train"], color="#4C78A8", label="训练准确率")
    ax.plot(history["val"], color="#E45756", label="验证准确率")
    ax.set_title(name)
    ax.set_ylim(0.4, 1.02)
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8)

for ax in axes[1]:
    ax.set_xlabel("epoch")
for ax in axes[:, 0]:
    ax.set_ylabel("准确率")

fig.suptitle("四种配置的训练与验证准确率", y=1.01)
fig.tight_layout()
fig.savefig(out / "regularization.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "regularization.png")))
plt.close(fig)

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
    X, y, test_size=0.3, random_state=42, stratify=y
)

mean = X_train.mean(axis=0)
std = X_train.std(axis=0) + 1e-6
X_train_t = torch.from_numpy((X_train - mean) / std)
X_val_t = torch.from_numpy((X_val - mean) / std)
y_train_t = torch.from_numpy(y_train)
y_val_t = torch.from_numpy(y_val)

print("训练集:", X_train_t.shape, "验证集:", X_val_t.shape)
print("训练集标签分布:", torch.bincount(y_train_t).tolist())
print("像素范围:", round(float(X.min()), 1), "到", round(float(X.max()), 1))


logits = torch.tensor([[2.0, 0.5], [0.1, 1.7]])
probs = torch.softmax(logits, dim=1)

print("logits:")
print(logits)
print("概率:")
print(probs)
print("每行概率和:", probs.sum(dim=1))

target = torch.tensor([1, 1])
loss = F.cross_entropy(logits, target)
manual = -torch.log(probs[torch.arange(2), target]).mean()
print("cross_entropy:", round(loss.item(), 4))
print("手算负对数似然:", round(manual.item(), 4))


torch.manual_seed(42)

model = torch.nn.Linear(64, 2)
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

train_losses, val_losses, val_accs = [], [], []

for epoch in range(1, 13):
    model.train()
    perm = torch.randperm(len(X_train_t))
    epoch_loss = 0.0
    for start in range(0, len(perm), 32):
        idx = perm[start:start + 32]
        xb, yb = X_train_t[idx], y_train_t[idx]
        optimizer.zero_grad()
        loss = F.cross_entropy(model(xb), yb)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item() * len(idx)

    model.eval()
    with torch.no_grad():
        train_loss = epoch_loss / len(X_train_t)
        val_logits = model(X_val_t)
        val_loss = F.cross_entropy(val_logits, y_val_t).item()
        val_acc = (val_logits.argmax(dim=1) == y_val_t).float().mean().item()

    train_losses.append(train_loss)
    val_losses.append(val_loss)
    val_accs.append(val_acc)

    if epoch % 2 == 0:
        print(f"epoch {epoch:02d}  训练损失 {train_loss:.3f}  验证损失 {val_loss:.3f}  验证准确率 {val_acc:.3f}")


model.eval()
with torch.no_grad():
    probs = torch.softmax(model(X_val_t), dim=1).numpy()
    pred = probs.argmax(axis=1)

print("验证准确率:", round(float((pred == y_val).mean()), 4))
print("\n前 5 个样本:")
for i in range(5):
    print(f"  真实 {y_val[i]}  预测 {pred[i]}  属于 8 的概率 {probs[i, 1]:.3f}")

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].hist(probs[y_val == 0, 1], bins=20, alpha=0.7, color="#4C78A8", label="真实类别 3")
axes[0].hist(probs[y_val == 1, 1], bins=20, alpha=0.6, color="#F58518", label="真实类别 8")
axes[0].set_xlabel("模型给出的属于 8 的概率")
axes[0].set_ylabel("样本数")
axes[0].set_title("概率分布")
axes[0].legend()
axes[0].spines[["top", "right"]].set_visible(False)

axes[1].plot(train_losses, color="#4C78A8", label="训练损失")
axes[1].plot(val_losses, color="#E45756", label="验证损失")
axes[1].set_xlabel("epoch")
axes[1].set_ylabel("交叉熵")
axes[1].set_title("损失曲线")
axes[1].legend()
axes[1].spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "softmax-probability.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "softmax-probability.png")))
plt.close(fig)

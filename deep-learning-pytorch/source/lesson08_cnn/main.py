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
from torch import nn

print("PyTorch:", torch.__version__)
print("输出目录:", out)


x = torch.randn(2, 1, 8, 8)
conv = nn.Conv2d(1, 4, kernel_size=3, padding=1)
pool = nn.MaxPool2d(2)

conv_out = conv(x)
pool_out = pool(conv_out)

print("输入:", tuple(x.shape))
print("卷积后:", tuple(conv_out.shape))
print("池化后:", tuple(pool_out.shape))
print("卷积核权重:", tuple(conv.weight.shape))
print("卷积核偏置:", tuple(conv.bias.shape))

print("\n尺寸计算: (8 + 2*1 - 3) / 1 + 1 =", (8 + 2 * 1 - 3) // 1 + 1)


# 两层 3x3 卷积，输出尺寸不变，但感受野从 3 扩大到 5
# 这里只看卷积的覆盖范围，先不加激活函数
two_layer = nn.Sequential(
    nn.Conv2d(1, 4, kernel_size=3, padding=1, bias=False),
    nn.Conv2d(4, 4, kernel_size=3, padding=1, bias=False),
)
two_layer_out = two_layer(torch.randn(1, 1, 8, 8))
print("两层卷积后的形状:", tuple(two_layer_out.shape))

# 用 1 个像素的输入检查第二层中心位置能影响多少输出
probe = torch.zeros(1, 1, 8, 8)
probe[0, 0, 4, 4] = 1.0
response = two_layer(probe)
affected = (response.abs().sum(dim=1) > 1e-6).sum().item()
print("受单个输入像素影响的输出位置数:", affected)


digits = load_digits()
mask = (digits.target == 3) | (digits.target == 8)
X = digits.data[mask].astype("float32")
y = (digits.target[mask] == 8).astype("int64")

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

mean = X_train.mean(axis=0)
std = X_train.std(axis=0) + 1e-6
X_train_t = torch.from_numpy(((X_train - mean) / std).reshape(-1, 1, 8, 8))
X_val_t = torch.from_numpy(((X_val - mean) / std).reshape(-1, 1, 8, 8))
y_train_t = torch.from_numpy(y_train)
y_val_t = torch.from_numpy(y_val)

print("训练集:", tuple(X_train_t.shape), "验证集:", tuple(X_val_t.shape))


sample = X_val_t[0:1]
edge_kernel = torch.tensor([[[[-1.0, -1.0, -1.0],
                              [-1.0, 8.0, -1.0],
                              [-1.0, -1.0, -1.0]]]])
edge = F.conv2d(sample, edge_kernel, padding=1)

fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
axes[0].imshow(X_val[0].reshape(8, 8), cmap="gray")
axes[0].set_title("原始图像")
axes[1].imshow(edge_kernel[0, 0].numpy(), cmap="RdBu_r")
axes[1].set_title("边缘检测核")
axes[2].imshow(edge[0, 0].detach().numpy(), cmap="RdBu_r")
axes[2].set_title("卷积响应")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(out / "conv-kernel.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "conv-kernel.png")))
plt.close(fig)


torch.manual_seed(42)

cnn = nn.Sequential(
    nn.Conv2d(1, 8, kernel_size=3, padding=1),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Conv2d(8, 16, kernel_size=3, padding=1),
    nn.ReLU(),
    nn.MaxPool2d(2),
    nn.Flatten(),
    nn.Linear(16 * 2 * 2, 2),
)

optimizer = torch.optim.Adam(cnn.parameters(), lr=1e-3)
losses = []

for epoch in range(1, 7):
    cnn.train()
    perm = torch.randperm(len(X_train_t))
    epoch_loss = 0.0
    for start in range(0, len(perm), 32):
        idx = perm[start:start + 32]
        optimizer.zero_grad()
        loss = F.cross_entropy(cnn(X_train_t[idx]), y_train_t[idx])
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item() * len(idx)

    cnn.eval()
    with torch.no_grad():
        train_acc = (cnn(X_train_t).argmax(dim=1) == y_train_t).float().mean().item()
        val_acc = (cnn(X_val_t).argmax(dim=1) == y_val_t).float().mean().item()

    losses.append(epoch_loss / len(X_train_t))
    print(f"epoch {epoch}  损失 {losses[-1]:.3f}  训练准确率 {train_acc:.3f}  验证准确率 {val_acc:.3f}")


first_conv = cnn[0]
with torch.no_grad():
    feature_maps = first_conv(sample)

fig, axes = plt.subplots(1, 5, figsize=(12, 2.8))
axes[0].imshow(X_val[0].reshape(8, 8), cmap="gray")
axes[0].set_title("原始图像")
for i in range(4):
    axes[i + 1].imshow(feature_maps[0, i].detach().numpy(), cmap="viridis")
    axes[i + 1].set_title(f"特征图 {i + 1}")
for ax in axes:
    ax.axis("off")
fig.tight_layout()
fig.savefig(out / "feature-maps.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "feature-maps.png")))
plt.close(fig)

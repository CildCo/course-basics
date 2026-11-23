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

from torch import nn
from torch.utils.data import DataLoader, TensorDataset

print("PyTorch:", torch.__version__)
print("输出目录:", out)


torch.manual_seed(7)

x = torch.linspace(-2, 2, 240).unsqueeze(1)
y = 0.5 * x ** 3 - x + 0.4 * torch.randn_like(x)
features = torch.cat([x, x ** 2, x ** 3], dim=1)

generator = torch.Generator().manual_seed(42)
perm = torch.randperm(len(x), generator=generator)
train_idx, val_idx = perm[:192], perm[192:]

X_train, y_train = features[train_idx], y[train_idx]
X_val, y_val = features[val_idx], y[val_idx]

# 标准化参数只能从训练集计算
mean = X_train.mean(dim=0, keepdim=True)
std = X_train.std(dim=0, keepdim=True)
X_train = (X_train - mean) / std
X_val = (X_val - mean) / std

print("训练集:", tuple(X_train.shape), "验证集:", tuple(X_val.shape))
print("特征均值:", torch.round(mean, decimals=3).squeeze().tolist())
print("特征标准差:", torch.round(std, decimals=3).squeeze().tolist())


train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(
    train_dataset,
    batch_size=16,
    shuffle=True,
    generator=torch.Generator().manual_seed(0),
)

print("每批样本数: 16")
print("每个 epoch 的批次数:", len(train_loader))

for batch_x, batch_y in train_loader:
    print("第一批形状:", tuple(batch_x.shape), tuple(batch_y.shape))
    break


torch.manual_seed(42)

model = nn.Linear(3, 1)
loss_fn = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.02)

best_val = float("inf")
best_epoch = 0
best_state = None
wait = 0
patience = 10
history = {"train": [], "val": []}

for epoch in range(1, 121):
    model.train()
    total_loss = 0.0
    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        loss = loss_fn(model(batch_x), batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(batch_x)

    train_loss = total_loss / len(X_train)
    model.eval()
    with torch.no_grad():
        val_loss = loss_fn(model(X_val), y_val).item()

    history["train"].append(train_loss)
    history["val"].append(val_loss)

    if val_loss < best_val - 1e-5:
        best_val = val_loss
        best_epoch = epoch
        best_state = {key: value.detach().clone() for key, value in model.state_dict().items()}
        wait = 0
    else:
        wait += 1
        if wait >= patience:
            print(f"第 {epoch} 轮触发早停，最佳轮次是第 {best_epoch} 轮")
            break

model.load_state_dict(best_state)
print("最佳验证损失:", round(best_val, 4))
print("最佳轮次:", best_epoch)


from IPython.display import Image, display
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7.5, 4))
ax.plot(history["train"], color="#4C78A8", label="训练损失")
ax.plot(history["val"], color="#E45756", label="验证损失")
ax.axvline(best_epoch - 1, color="#54A24B", linestyle="--", label=f"最佳轮次 {best_epoch}")
ax.set_xlabel("epoch")
ax.set_ylabel("均方误差")
ax.set_title("训练损失与验证损失")
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "train-val-curve.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "train-val-curve.png")))
plt.close(fig)


print("恢复后的参数:")
for name, param in model.named_parameters():
    print(f"  {name}: {torch.round(param.detach(), decimals=3).squeeze().tolist()}")

model.eval()
with torch.no_grad():
    pred = model(X_val[:5]).squeeze()
print("\n前 5 个验证样本:")
for true_value, pred_value in zip(y_val[:5].flatten().tolist(), pred.tolist()):
    print(f"  真实 {true_value:+.3f}  预测 {pred_value:+.3f}")

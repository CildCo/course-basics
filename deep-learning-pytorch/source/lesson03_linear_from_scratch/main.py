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

print("PyTorch:", torch.__version__)
print("输出目录:", out)


torch.manual_seed(42)

x = torch.linspace(-1, 1, 120).unsqueeze(1)
w_true, b_true = 3.0, 2.0
y = w_true * x + b_true + 0.3 * torch.randn_like(x)

print("x 的形状:", x.shape)
print("y 的形状:", y.shape)
print("前 3 条数据:")
for xi, yi in zip(x[:3], y[:3]):
    print(f"  x={xi.item():.3f}, y={yi.item():.3f}")


w = torch.zeros(1, 1, requires_grad=True)
b = torch.zeros(1, requires_grad=True)

def mse_loss(pred, target):
    return ((pred - target) ** 2).mean()

pred = x @ w + b
loss = mse_loss(pred, y)

print("初始预测前 3 个:", pred[:3].squeeze().tolist())
print("初始损失:", loss.item())


learning_rate = 0.5
losses = []

for epoch in range(8):
    pred = x @ w + b
    loss = mse_loss(pred, y)

    loss.backward()

    with torch.no_grad():
        w -= learning_rate * w.grad
        b -= learning_rate * b.grad

    w.grad.zero_()
    b.grad.zero_()
    losses.append(loss.item())

print("训练完成")
print("学习到的 w:", round(w.item(), 3), "真实值:", w_true)
print("学习到的 b:", round(b.item(), 3), "真实值:", b_true)
print("初始损失:", round(losses[0], 3))
print("最终损失:", round(losses[-1], 3))


def train(lr, epochs=8):
    torch.manual_seed(0)
    w = torch.zeros(1, 1, requires_grad=True)
    b = torch.zeros(1, requires_grad=True)
    history = []
    for _ in range(epochs):
        pred = x @ w + b
        loss = mse_loss(pred, y)
        loss.backward()
        with torch.no_grad():
            w -= lr * w.grad
            b -= lr * b.grad
        w.grad.zero_()
        b.grad.zero_()
        history.append(loss.item())
    return history

for lr in [0.01, 0.5, 1.2]:
    history = train(lr)
    print(f"学习率 {lr:<4} 最终损失 {history[-1]:.4f}  首轮损失 {history[0]:.2f}")


from IPython.display import Image, display
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(11, 4))

axes[0].plot(losses, color="#4C78A8")
axes[0].set_xlabel("迭代轮次")
axes[0].set_ylabel("均方误差")
axes[0].set_title("损失曲线")
axes[0].spines[["top", "right"]].set_visible(False)

axes[1].scatter(x.numpy(), y.numpy(), s=14, alpha=0.55, color="#8C8C8C", label="样本")
x_line = torch.linspace(-1, 1, 2).unsqueeze(1)
y_line = x_line @ w + b
axes[1].plot(x_line.detach().numpy(), y_line.detach().numpy(), color="#E45756", linewidth=2, label="拟合直线")
axes[1].set_xlabel("x")
axes[1].set_ylabel("y")
axes[1].set_title("拟合结果")
axes[1].legend()
axes[1].spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(out / "linear-scratch.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "linear-scratch.png")))
plt.close(fig)

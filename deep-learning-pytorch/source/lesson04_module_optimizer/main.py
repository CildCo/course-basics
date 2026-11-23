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

print("PyTorch:", torch.__version__)
print("输出目录:", out)


torch.manual_seed(42)

x = torch.linspace(-1, 1, 120).unsqueeze(1)
y = 3.0 * x + 2.0 + 0.3 * torch.randn_like(x)

print("训练样本:", x.shape[0], "条")
print("x 范围:", round(x.min().item(), 2), "到", round(x.max().item(), 2))


class LinearRegression(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)

    def forward(self, x):
        return self.linear(x)


model = LinearRegression()
print(model)
print("参数列表:")
for name, param in model.named_parameters():
    print(f"  {name}: {tuple(param.shape)}")

print("state_dict:")
for name, value in model.state_dict().items():
    print(f"  {name}: {value.tolist()}")


def train(model, optimizer, epochs=80):
    loss_fn = nn.MSELoss()
    history = []

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        pred = model(x)
        loss = loss_fn(pred, y)
        loss.backward()
        optimizer.step()

        history.append(loss.item())

    return history


torch.manual_seed(42)
sgd_model = LinearRegression()
sgd_optimizer = torch.optim.SGD(sgd_model.parameters(), lr=0.2)
sgd_losses = train(sgd_model, sgd_optimizer)

print("SGD 权重:", round(sgd_model.linear.weight.item(), 3))
print("SGD 偏置:", round(sgd_model.linear.bias.item(), 3))
print("SGD 最终损失:", round(sgd_losses[-1], 4))


torch.manual_seed(42)
adam_model = LinearRegression()
adam_optimizer = torch.optim.Adam(adam_model.parameters(), lr=0.1)
adam_losses = train(adam_model, adam_optimizer)

print("Adam 权重:", round(adam_model.linear.weight.item(), 3))
print("Adam 偏置:", round(adam_model.linear.bias.item(), 3))
print("Adam 最终损失:", round(adam_losses[-1], 4))

print("\n对比:")
print(f"{'优化器':<6}{'权重':>8}{'偏置':>8}{'首轮损失':>10}{'最终损失':>10}")
for name, model, history in [("SGD", sgd_model, sgd_losses), ("Adam", adam_model, adam_losses)]:
    print(f"{name:<6}{model.linear.weight.item():>8.3f}{model.linear.bias.item():>8.3f}"
          f"{history[0]:>10.3f}{history[-1]:>10.3f}")


from IPython.display import Image, display
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7.5, 4))
ax.plot(sgd_losses, color="#4C78A8", label="SGD, lr=0.2")
ax.plot(adam_losses, color="#F58518", label="Adam, lr=0.1")
ax.set_xlabel("迭代轮次")
ax.set_ylabel("均方误差")
ax.set_title("SGD 与 Adam 的收敛过程")
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "sgd-vs-adam.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "sgd-vs-adam.png")))
plt.close(fig)

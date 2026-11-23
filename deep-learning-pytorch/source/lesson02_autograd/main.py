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


x = torch.tensor(2.0, requires_grad=True)
y = x ** 3 + 2 * x + 1

print("y =", y)
print("y 的 grad_fn:", y.grad_fn)

y.backward()
print("自动求导结果:", x.grad)
print("解析结果:", 3 * 2.0 ** 2 + 2)


x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
w = torch.tensor([0.5, -1.0, 2.0], requires_grad=True)
b = torch.tensor(1.0, requires_grad=True)

z = (x * w).sum() + b
z.backward()

print("z =", z.item())
print("x.grad =", x.grad)
print("w.grad =", w.grad)
print("b.grad =", b.grad)

# 再算一遍，梯度会累加
z2 = (x * w).sum()
z2.backward()
print("第二次 backward 后 x.grad =", x.grad)

x.grad.zero_()
print("清零后 x.grad =", x.grad)


x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
y = x * 2

print("普通计算 requires_grad:", y.requires_grad)

with torch.no_grad():
    z = x * 2
print("no_grad 中 requires_grad:", z.requires_grad)

detached = y.detach()
print("detach 后 requires_grad:", detached.requires_grad)
print("数据是否共享:", detached.data_ptr() == y.data_ptr())

try:
    detached.backward()
except RuntimeError as error:
    print("对 detach 结果求导会报错:", str(error).splitlines()[0])


from IPython.display import Image, display
import matplotlib.pyplot as plt

xs = torch.linspace(-3, 3, 120)
ys = xs ** 2

x0 = 1.0
y0 = x0 ** 2
slope = 2 * x0
tangent = y0 + slope * (xs - x0)

# 用自动求导再验证一次
x_check = torch.tensor(x0, requires_grad=True)
(x_check ** 2).backward()
print("自动求导:", x_check.grad.item(), "解析导数:", slope)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(xs.numpy(), ys.numpy(), color="#4C78A8", linewidth=2, label="f(x) = x²")
ax.plot(xs.numpy(), tangent.numpy(), color="#F58518", linestyle="--", label="x=1 处的切线")
ax.scatter([x0], [y0], color="#E45756", zorder=3)
ax.annotate(f"斜率 = {slope:.0f}", xy=(x0, y0), xytext=(1.5, 5),
            arrowprops={"arrowstyle": "->", "color": "#666666"})
ax.set_xlabel("x")
ax.set_ylabel("f(x)")
ax.set_title("导数就是切线的斜率")
ax.legend()
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(out / "tangent.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "tangent.png")))
plt.close(fig)

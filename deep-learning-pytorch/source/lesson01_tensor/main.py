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
print("CUDA 可用:", torch.cuda.is_available())
print("素材目录约定:", data_path("README.md").parent)
print("输出目录:", out)


scalar = torch.tensor(3.0)
vector = torch.tensor([1.0, 2.0, 3.0])
matrix = torch.arange(12).reshape(3, 4)

for name, t in [("标量", scalar), ("向量", vector), ("矩阵", matrix)]:
    print(f"{name}: shape={tuple(t.shape)}, dtype={t.dtype}, device={t.device}")
    print(t)
    print("-" * 40)


labels = torch.tensor([0, 1, 1, 0])
print("标签:", labels.dtype)

as_float = labels.float()
print("转成浮点:", as_float.dtype)

back_to_int = as_float.long()
print("再转回整数:", back_to_int.dtype, back_to_int)

print("矩阵的均值:", matrix.float().mean().item())
print("按列求和:", matrix.sum(dim=0))
print("按行求和:", matrix.sum(dim=1))


flat = matrix.reshape(-1)
print("展平:", flat.shape, flat)

image_batch = torch.arange(24).reshape(2, 1, 3, 4)
print("原始布局:", image_batch.shape)

channels_last = image_batch.permute(0, 2, 3, 1)
print("通道后置:", channels_last.shape)

print("转置:", matrix.t().shape)
print("转置后是否连续:", matrix.t().is_contiguous())

try:
    matrix.t().view(-1)
except RuntimeError as error:
    print("view 失败原因:", str(error).splitlines()[0])

print("reshape 可以处理:", matrix.t().reshape(-1).shape)


a = torch.arange(6).reshape(2, 3).float()
b = torch.tensor([10.0, 20.0, 30.0])

print("a:")
print(a)
print("a + b（b 广播到每一行）:")
print(a + b)

column = torch.tensor([[100.0], [200.0]])
print("a + column（column 广播到每一列）:")
print(a + column)

weights = torch.randn(3, 2)
print("矩阵乘法:", (a @ weights).shape)

# 一批 4 张 3 通道的 8x8 图片，按通道做归一化
images = torch.randn(4, 3, 8, 8)
channel_mean = torch.tensor([0.5, 0.4, 0.3]).reshape(1, 3, 1, 1)
normalized = images - channel_mean
print("归一化前后:", images.shape, normalized.shape)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("使用设备:", device)

x = torch.randn(64, 784, device=device)
w = torch.randn(784, 10, device=device)
logits = x @ w

print("输入:", x.shape, x.device)
print("权重:", w.shape, w.device)
print("输出:", logits.shape, logits.device)

# 需要交给 NumPy 或 matplotlib 时，先转回 CPU
sample = logits[0].detach().cpu()
print("前 5 个分数:", torch.round(sample[:5], decimals=2))

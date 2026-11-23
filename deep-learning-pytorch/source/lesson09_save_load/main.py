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
import torch.nn.functional as F
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from torch import nn

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


class DigitMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
        )

    def forward(self, x):
        return self.net(x)


torch.manual_seed(42)
model = DigitMLP()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(1, 13):
    model.train()
    optimizer.zero_grad()
    loss = F.cross_entropy(model(X_train_t), y_train_t)
    loss.backward()
    optimizer.step()

    model.eval()
    with torch.no_grad():
        val_acc = (model(X_val_t).argmax(dim=1) == y_val_t).float().mean().item()
    if epoch % 3 == 0:
        print(f"epoch {epoch:02d}  损失 {loss.item():.3f}  验证准确率 {val_acc:.3f}")


model_path = out / "digit-mlp.pt"
checkpoint = {
    "state_dict": model.state_dict(),
    "mean": mean.tolist(),
    "std": std.tolist(),
    "classes": ["3", "8"],
    "version": "1.0.0",
    "val_accuracy": round(val_acc, 4),
    "torch_version": str(torch.__version__),
}
torch.save(checkpoint, model_path)

metadata = {key: value for key, value in checkpoint.items() if key != "state_dict"}
(out / "digit-mlp-meta.json").write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
)

digest = hashlib.sha256(model_path.read_bytes()).hexdigest()[:16]
print("检查点大小:", model_path.stat().st_size, "字节")
print("SHA256 前 16 位:", digest)
print("版本:", metadata["version"])
print("类别:", metadata["classes"])
print("验证准确率:", metadata["val_accuracy"])
print("预处理参数:", len(metadata["mean"]), "个均值 /", len(metadata["std"]), "个标准差")


loaded = torch.load(model_path, map_location="cpu", weights_only=True)
restored = DigitMLP()
restored.load_state_dict(loaded["state_dict"])
restored.eval()

print("版本:", loaded["version"])
print("类别:", loaded["classes"])
print("验证准确率:", loaded["val_accuracy"])

with torch.no_grad():
    original_logits = model.eval()(X_val_t[:5])
    restored_logits = restored(X_val_t[:5])

print("输出是否一致:", torch.allclose(original_logits, restored_logits))


@torch.no_grad()
def predict(model, raw_features, mean, std, classes):
    features = torch.from_numpy((raw_features - mean) / std)
    logits = model(features)
    probs = torch.softmax(logits, dim=1)
    pred = probs.argmax(dim=1)
    labels = [classes[index] for index in pred.tolist()]
    return labels, probs.max(dim=1).values


loaded_mean = np.array(loaded["mean"], dtype="float32")
loaded_std = np.array(loaded["std"], dtype="float32")
labels, confidence = predict(restored, X_val[:5], loaded_mean, loaded_std, loaded["classes"])

print("前 5 个验证样本:")
for true_label, pred_label, score in zip(y_val[:5], labels, confidence.tolist()):
    print(f"  真实 {true_label}  预测 {pred_label}  置信度 {score:.3f}")


from IPython.display import Image, display
import matplotlib.pyplot as plt

labels, confidence = predict(restored, X_val[:8], loaded_mean, loaded_std, loaded["classes"])

fig, axes = plt.subplots(2, 4, figsize=(9, 4.8))
for ax, image, true_label, pred_label, score in zip(
    axes.flat, X_val[:8], y_val[:8], labels, confidence.tolist()
):
    ax.imshow(image.reshape(8, 8), cmap="gray")
    ok = str(true_label) == pred_label
    ax.set_title(f"真 {true_label} / 预 {pred_label}\n{score:.2f}", fontsize=9,
                 color="#2A6F4E" if ok else "#B23A3A")
    ax.axis("off")
fig.tight_layout()
fig.savefig(out / "inference-samples.png", dpi=120, bbox_inches="tight")
display(Image(filename=str(out / "inference-samples.png")))
plt.close(fig)

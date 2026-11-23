import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class Traced:
    def __init__(self, name):
        self.name = name

    def __getattribute__(self, attr):
        print(f"[getattribute] {attr}")
        return object.__getattribute__(self, attr)

    def __getattr__(self, attr):
        print(f"[getattr] {attr}")
        if attr.startswith("metric_"):
            return attr.removeprefix("metric_").upper()
        raise AttributeError(f"没有属性 {attr}")


obj = Traced("demo")
print("name =", obj.name)
print("metric_latency =", obj.metric_latency)
try:
    obj.missing
except AttributeError as exc:
    print("missing ->", exc)


class Settings:
    def __init__(self, values):
        object.__setattr__(self, "_values", dict(values))

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        values = object.__getattribute__(self, "_values")
        try:
            return values[name]
        except KeyError as exc:
            raise AttributeError(f"配置项 {name} 不存在") from exc


cfg = Settings({"timeout": 3, "retries": 2})
print(cfg.timeout, cfg.retries)
print("timeout" in cfg._values)
print(hasattr(cfg, "endpoint"))
print(getattr(cfg, "endpoint", "http://localhost"))


class SafeSecrets:
    def __getattribute__(self, name):
        if name.startswith("secret_"):
            raise AttributeError("secret fields are hidden")
        return object.__getattribute__(self, name)


class Naive:
    def __getattribute__(self, name):
        return self.__dict__[name]


safe = SafeSecrets()
safe.public = "ok"
print("public =", safe.public)
try:
    safe.secret_token
except AttributeError as exc:
    print("secret ->", exc)

naive = Naive()
naive.value = 10
try:
    naive.value
except Exception as exc:
    print("Naive ->", type(exc).__name__)


from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from IPython.display import Image, display

out = Path.cwd() / "output"
out.mkdir(exist_ok=True)

steps = [
    ("obj.x", "#cfe3f7"),
    ("__getattribute__ wraps every access", "#f6d9a8"),
    ("data descriptor (defines __set__)", "#d9ead3"),
    ("instance __dict__", "#d9ead3"),
    ("class attribute / non-data descriptor", "#d9ead3"),
    ("__getattr__ fallback", "#f4cccc"),
    ("AttributeError", "#eeeeee"),
]
fig, ax = plt.subplots(figsize=(9.5, 5.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6.2)
ax.axis("off")
y = 5.75
for index, (label, color) in enumerate(steps):
    ax.add_patch(
        FancyBboxPatch(
            (2.0, y - 0.34),
            6.0,
            0.58,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor=color,
            edgecolor="#555555",
            linewidth=1,
        )
    )
    ax.text(5.0, y - 0.05, label, ha="center", va="center", fontsize=10)
    if index < len(steps) - 1:
        ax.annotate(
            "",
            xy=(5.0, y - 0.45),
            xytext=(5.0, y - 0.60),
            arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.2),
        )
    y -= 0.91
ax.text(8.25, 5.2, "a hit returns immediately", fontsize=9, color="#444444")
ax.text(8.25, 2.57, "all misses reach the fallback", fontsize=9, color="#444444")
ax.set_title("Python attribute lookup path", fontsize=13, pad=8)
fig.tight_layout()
image_path = out / "01-lookup-path.png"
fig.savefig(image_path, dpi=140, bbox_inches="tight")
plt.close(fig)
display(Image(filename=str(image_path)))


report = out / "01-attribute-report.txt"
report.write_text(
    "属性协议检查\n"
    "1. __getattribute__ 每次访问都会运行\n"
    "2. __getattr__ 只在默认查找失败后运行\n"
    "3. 覆盖 __getattribute__ 时必须委托给 object.__getattribute__\n",
    encoding="utf-8",
)
print(report.read_text(encoding="utf-8"))

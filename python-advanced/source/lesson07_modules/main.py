import sys
import math

print(math.sqrt(16))
print(sys.version_info[:2])
print(len(sys.path))


from pathlib import Path
import sys

output = Path("output")
output.mkdir(exist_ok=True)
(output / "mytools.py").write_text(
    "def double(n):\n    return n * 2\n",
    encoding="utf-8",
)
sys.path.insert(0, str(output.resolve()))

import mytools

print(mytools.double(21))


package = output / "shop"
package.mkdir(exist_ok=True)
(package / "__init__.py").write_text("", encoding="utf-8")
(package / "pricing.py").write_text(
    "def with_tax(price, rate=0.13):\n    return round(price * (1 + rate), 2)\n",
    encoding="utf-8",
)

from shop.pricing import with_tax

print(with_tax(100))


print("创建环境：python -m venv .venv")
print("激活 Windows：.venv\\Scripts\\activate")
print("安装依赖：pip install -r requirements.txt")
print("导出依赖：pip freeze > requirements.txt")

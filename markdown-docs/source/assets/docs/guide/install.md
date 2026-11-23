---
title: 安装与准备
nav: 安装
order: 2
summary: 装好 Python 依赖，认准文档、资源和输出三个目录。
tags:
  - 环境
  - 依赖
---

# 安装与准备

## 环境要求

| 组件 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.10 以上 | 运行生成脚本 |
| markdown | 3.5 以上 | 把 Markdown 转成 HTML |
| Jinja2 | 3.1 以上 | 套用页面模板 |
| PyYAML | 6.0 以上 | 读取 front matter |

## 安装步骤

```bash
python -m pip install markdown jinja2 PyYAML
```

### 检查版本

```python
import markdown, jinja2, yaml
print(markdown.__version__, jinja2.__version__, yaml.__version__)
```

看到三个版本号就说明依赖装好了。版本不用完全一致，只要能被导入。

## 目录约定

把文档放在 `docs/` 下，生成的页面统一写到 `output/`。

- `docs/` 保存源文件。
- `output/` 保存生成结果，可以随时删除重建。
- 不要把 `output/` 提交到版本库。

## 下一步

装好依赖后，按 [写作流程](workflow.md) 改一篇文档试试。遇到问题先看 [常见问题](../faq.md)。

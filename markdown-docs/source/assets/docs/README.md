---
title: 课程文档站
nav: 首页
order: 1
summary: 一套只有五个文件的示例文档，演示从 Markdown 到静态站点的完整流程。
tags:
  - 文档
  - 示例
---

# 课程文档站

这套文档是课程里的示例项目。文件不多，但覆盖了写作、链接、元数据和发布四件事。

## 这个站点包含什么

- [安装与准备](guide/install.md)：环境要求和目录约定。
- [写作流程](guide/workflow.md)：从建分支到预览发布的步骤。
- [语法速查](reference/syntax.md)：标题、列表、代码、表格和锚点。
- [常见问题](faq.md)：链接、元数据和样式的排查方法。

## 目录结构

```text
docs/
├── README.md
├── faq.md
├── guide/
│   ├── install.md
│   └── workflow.md
└── reference/
    └── syntax.md
```

## 先约定三件事

1. 文件名用小写英文和短横线，避免空格和大写。
2. 每篇文档都有 front matter，至少写 title、nav、order、summary。
3. 站内链接一律用相对路径，不写绝对路径。

> 文档不是写给自己看的。读者第一次打开时，应该能在一分钟内找到入口。

## 写完怎么检查

- 用 `python -m markdown` 预览单篇。
- 用课程里的链接检查脚本扫一遍相对链接。
- 用 `python build_site.py` 生成整站后逐页点开。

更多细节见 [写作流程](guide/workflow.md#一次完整的修改流程)。

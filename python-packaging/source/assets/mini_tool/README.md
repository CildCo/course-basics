# wordmeter

统计文本文件的行数、词数和字符数，适合检查稿件长度和批量文本体积。

## 安装

```bash
python -m pip install wordmeter-0.1.0-py3-none-any.whl
```

## 使用

```bash
wordmeter article.txt
wordmeter article.txt --json
cat article.txt | wordmeter
```

## 输出字段

| 字段 | 含义 |
| --- | --- |
| lines | 行数，最后一行没有换行符也算一行 |
| words | 英文单词数与中文汉字数之和 |
| chars | 全部字符数 |
| cjk | 中文字符数 |

## 开发

源码使用 `src/` 布局，构建时把 `src/` 加入包搜索路径：

```bash
python -m pip wheel . --no-deps --no-build-isolation -w dist
```

## 许可

MIT

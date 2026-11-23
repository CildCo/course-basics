# pipeline-demo

课程用的最小 Python 项目，提供版本号解析、递增、发布标签、制品命名和校验和函数。

```bash
python -m pytest
python -m pip wheel . --no-deps --no-build-isolation -w dist
```

`pip wheel` 只在本地用已安装的 setuptools 和 wheel 打包，不需要联网。

# FastAPI 进阶：认证、数据库与测试

- 类型：编程基础
- 难度：高级

## 运行

```bash
python run_all.py
```

## 课程大纲

1. 第1课 从单文件到分层：routers、schemas、services、db
2. 第2课 配置与环境变量：pydantic-settings 或标准库方案
3. 第3课 Pydantic 模型：请求、响应、校验与序列化
4. 第4课 SQLite + SQLAlchemy：会话、模型与 CRUD
5. 第5课 依赖注入：把数据库会话和当前用户注入路由
6. 第6课 密码哈希：PBKDF2 与盐（只用标准库 hashlib/secrets）
7. 第7课 JWT 登录与权限：PyJWT 签发、校验、过期
8. 第8课 分页、过滤与统一错误处理
9. 第9课 测试：TestClient、临时数据库、依赖覆盖
10. 第10课 项目：带注册登录的待办 API

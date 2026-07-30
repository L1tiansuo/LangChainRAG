---
name: test
description: 对代码创建单元测试，执行测试，生成测试报告。
---

# 单元测试

对 RAG 企业知识库问答系统编写并运行单元测试。

## 参数

- 无参数 → 运行全部测试（后端 + 前端），输出报告
- `backend` → 只运行后端 Pytest 测试
- `frontend` → 只运行前端 Vitest 测试
- `<文件路径>` → 只运行指定测试文件
- `new <源文件路径>` → 为指定源文件创建新的测试文件

## 测试框架

| 层级 | 工具 | 用途 |
|------|------|------|
| 后端 | Pytest + pytest-asyncio + httpx | FastAPI 异步 API 测试 |
| 前端 | Vitest | React 组件/工具函数测试 |

## 执行流程

### 运行全部测试

**后端**：
```bash
cd backend && python -m pytest tests/ -v --tb=short
```

**前端**：
```bash
cd frontend && npx vitest run --reporter=verbose
```

### 运行后端测试

```bash
cd backend && python -m pytest tests/ -v --tb=short
```

### 运行前端测试

```bash
cd frontend && npx vitest run --reporter=verbose
```

### 运行特定文件

```bash
# 后端
cd backend && python -m pytest <文件路径> -v --tb=short

# 前端
cd frontend && npx vitest run --reporter=verbose <文件路径>
```

### 创建新测试

1. 读取源文件，分析导出的函数/API 端点/服务逻辑
2. 根据技术栈在对应目录创建测试文件：
   - 后端 → `backend/tests/test_<模块名>.py`
   - 前端 → `frontend/src/__tests__/<模块名>.test.ts`
3. 写完后自动运行验证所有测试通过
4. **重点测试**：API 端点的请求/响应、服务层业务逻辑、权限控制、边界条件

## 测试报告

运行结束后，汇报：

- 测试文件数、通过数、失败数
- 总耗时
- 如果有失败，逐个列出：
  - 哪个文件的哪个测试
  - 期望值 vs 实际值
  - 给出修复建议

## 现有测试

| 文件 | 覆盖内容 |
|------|---------|
| `backend/tests/test_auth.py` | 认证 API（注册/登录/密码修改/权限） |
| `backend/tests/test_sessions.py` | 会话管理 API |
| `backend/tests/test_chat.py` | 聊天问答 API |
| `backend/tests/test_kb.py` | 知识库管理 API |
| `backend/tests/test_rag.py` | RAG 流水线（检索/引文/记忆） |

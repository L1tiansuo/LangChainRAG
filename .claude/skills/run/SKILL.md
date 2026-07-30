---
name: run
description: 启动 RAG 知识库问答系统。默认前后端同时启动，支持单独启动。
---

# 启动 RAG 系统

启动后端 FastAPI 服务和前端 React 开发服务器。

## 参数

- 无参数 / `all` → 前后端同时启动
- `backend` / `后端` → 只启动后端（端口 8000）
- `frontend` / `前端` → 只启动前端（端口 5173）

## 执行流程

### 1. 前置检查

检查环境是否就绪：

```bash
python --version && node --version
```

- Python 不可用 → 提示安装 Python 3.10+
- Node.js 不可用 → 提示安装 Node.js 18+

检查 `backend/data/app.db` 是否存在：
- 不存在 → 先运行 `cd backend && python init_db.py`
- 存在 → 跳过初始化

检查 `frontend/node_modules/` 是否存在：
- 不存在 → 先运行 `cd frontend && npm install`

### 2. 启动服务

#### 全部启动（默认）

直接运行项目启动脚本：
```bash
python start.py
```

#### 单独启动后端

```bash
cd backend && python run.py
```

后端会在 `http://localhost:8000` 启动，API 文档在 `http://localhost:8000/docs`。

#### 单独启动前端

```bash
cd frontend && npm run dev
```

前端会在 `http://localhost:5173` 启动（如端口被占用则自动换 5174/5175）。

### 3. 完成后

告知用户：
- 前端页面: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 管理员账号: admin / 123456
- 停止方式: 双击 stop.bat 或 Ctrl+C

## 注意事项

- 如果后端启动失败，检查 `.env` 中的 `DASHSCOPE_API_KEY` 是否配置
- 端口 8000 被占用时，用 `stop.bat` 清理后重试
- 前端 Vite 首次启动需要预构建依赖，后续启动会很快

# RAG 企业知识库问答系统

基于 **LangChain** + **阿里云百炼**（通义千问）的 RAG 智能问答系统，面向电商商品知识库场景。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + LangChain + ChromaDB + SQLite |
| 前端 | React 19 + Ant Design 5 + Vite |
| LLM | 阿里云百炼 DashScope（qwen-plus / qwen-turbo / qwen-max） |
| 嵌入 | DashScope text-embedding-v4 |
| 测试 | Pytest + pytest-asyncio（43 用例） |

## 功能

- 🔐 用户注册 / 登录 / JWT 认证 / 角色权限
- 💬 多用户多会话管理 / 历史消息持久化
- 📄 知识库文档上传解析入库（PDF / DOCX / CSV / TXT / MD / HTML）
- 🤖 RAG 流式问答 + 知识库来源引用
- ⚡ 嵌入缓存 / 精排缓存 / 模型分级路由
- 🛠️ 管理员知识库管理 / 用户管理

## 快速启动

```bash
# 1. 配置 API Key
cp backend/.env.example backend/.env
# 编辑 backend/.env → 填入 DASHSCOPE_API_KEY

# 2. 初始化数据库
cd backend && python init_db.py

# 3. 启动（双击 start.bat 或手动）
python start.py
```

访问 `http://localhost:5173`，管理员账号 `admin` / `123456`。

## 停止

双击 `stop.bat`，或 `python stop.py`。

## 运行测试

```bash
cd backend && python -m pytest tests/ -v
```

## 项目结构

```
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── models/   # SQLAlchemy 模型
│   │   ├── schemas/  # Pydantic 校验
│   │   ├── services/ # 业务逻辑
│   │   ├── rag/      # RAG 流水线
│   │   ├── ingestion/# 文档解析入库
│   │   └── core/     # 基础设施
│   └── tests/        # Pytest 测试
├── frontend/         # React 前端
│   └── src/
│       ├── pages/    # 页面组件
│       ├── components/# UI 组件
│       ├── api/      # API 客户端
│       └── stores/   # Zustand 状态
└── scripts/          # 工具脚本
```

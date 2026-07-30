---
name: security-check
description: 安全审查：硬编码密钥、SQL 注入、XSS、敏感信息泄露、配置文件明文密码等。
---

# 安全审查

对 RAG 项目代码进行安全漏洞扫描。覆盖 Python 后端、TypeScript React 前端、配置文件。

## 参数

- 无参数 → 检查 `backend/` + `frontend/src/` + 配置文件
- `backend` / `后端` → 只检查 Python 后端
- `frontend` / `前端` → 只检查 TypeScript 前端
- `full` / `全面` → 扩展检查 + `npm audit` + `pip audit`

## 检查项目

### 一、敏感信息硬编码 🔑

| 风险项 | 检查关键词 | 风险等级 |
|--------|-----------|---------|
| API 密钥 | `api_key`, `apikey`, `DASHSCOPE_API_KEY`, `OPENAI_API_KEY`, `sk-` | 🔴 严重 |
| 密码 | 明文字符串形式的密码 | 🔴 严重 |
| Token | `jwt_secret`, `secret_key`, `JWT_SECRET_KEY` | 🔴 严重 |
| 数据库密码 | `DATABASE_URL` 中包含 `@` 和密码 | 🔴 严重 |
| 内网地址 | `192.168.`, `10.` 等 | 🟡 中等 |

重点检查 `.env` 是否在 `.gitignore` 中。

### 二、SQL 注入风险 🗄️

**Python 后端检查：**
- 是否有字符串拼接构造 SQL：`f"SELECT * FROM {table}"`
- 是否使用裸 `execute(text(...))` 而非参数化查询
- 正确做法：SQLAlchemy 的参数化查询 `select().where(Model.field == value)`

### 三、配置文件敏感信息 🗂️

| 文件 | 检查项 |
|------|--------|
| `.env` / `.env.example` | 是否被 git 追踪 |
| `backend/app/config.py` | 是否有硬编码的默认密钥 |
| `settings.local.json` | 是否暴露敏感路径 |

### 四、XSS 跨站脚本攻击 🖥️

**React 前端检查：**
| 风险点 | 说明 |
|--------|------|
| `dangerouslySetInnerHTML` | 极其危险 |
| `innerHTML` 直接赋值 | 检查是否绑定用户输入 |
| `eval()` / `new Function()` | 禁用 |
| `document.write()` | 禁用 |
| Markdown 渲染 | react-markdown 是否允许 HTML |

React 的 JSX `{}` 自动转义是安全的，不需要标记。

### 五、其他安全隐患

| 类型 | 检查项 |
|------|--------|
| 弱密码 | JWT_SECRET_KEY 是否为默认值 "change-this-..." |
| 调试泄露 | 生产代码中 `console.log` 打印敏感数据 |
| 文件上传 | 文件类型白名单是否完整、大小限制 |
| CORS | CORS_ORIGINS 是否为 `*`（允许所有来源） |
| 依赖漏洞 | `pip list --outdated`、`npm audit` |

## 报告格式

```
🔒 安全审查报告
═══════════════

🔴 严重 (N 处)
├─ 文件:行号 — 问题描述 + 修复建议

🟡 中等 (N 处)
├─ ...

═══════════════
📈 统计: 严重 N / 中等 N / 低风险 N
```

## 注意事项

- 只报告不修改，除非用户明确要求修复
- 检查 `.gitignore`：`.env`、`*.local` 是否被忽略
- 测试文件中的 mock 密钥标注为"测试数据"

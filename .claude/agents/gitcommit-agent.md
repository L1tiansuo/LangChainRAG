---
name: gitcommit-agent
description: 安全提交 — 先跑测试+质量审查，通过后自动存档推送
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Skill
  - Agent
---

# Git Commit Agent — 安全提交

并行运行 tester 和 qa-engineer 进行质量门禁检查，全部通过后自动调用 git-save 提交推送。

## 工作流程

### 1. 检查工作区

```bash
git status --porcelain
```

- 输出为空 → 回复"工作区干净，无需提交。"并结束。
- 有变更 → 记录变更文件列表，继续下一步。

### 2. 并行执行质量门禁

同时启动两个 agent：

```
Agent("tester", "运行全部后端单元测试，全部通过后写入 .claude/checkpoints/test-passed.json")

Agent("qa-engineer", "对项目代码进行质量审查，评分>=70且无严重问题时写入 .claude/checkpoints/qa-passed.json")
```

### 3. 验证门禁结果

检查两个标记文件是否存在：

```
验证项:
  ① .claude/checkpoints/test-passed.json 存在且 testsPassed == testsTotal
  ② .claude/checkpoints/qa-passed.json 存在且 score >= 70, critical == 0
```

### 4. 提交或拒绝

- **两个标记都有效 → 调用 `Skill("git-save")` 提交推送**
- **任一标记缺失或失败 → 报告哪个门禁未通过，拒绝提交**

### 5. 报告结果

**成功时：**
```
✅ 质量门禁通过
  测试: 43/43 通过
  质量: 85/100 (严重 0, 中等 2, 建议 3)
  → 正在提交...
```

**失败时：**
```
❌ 质量门禁未通过
  🔴 测试: X 失败
  🟢 质量: XX/100
拒绝提交。请修复后重试。
```

## 注意事项

- 不要跳过门禁直接 commit
- 如果标记文件是旧的（代码已变更），必须重新运行检查

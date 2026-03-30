---
name: second-brain-memory
description: |
  第二大脑记忆系统 - 个人长期知识存储与检索。
  使用FTS全文检索（无需向量模型），自动摘要/标签，三层归档（热/冷/冰），权限管理。
  
  触发场景（显式）：
  - "存入知识库"、"记一下这个"、"存入记忆库" → 存储记忆/知识
  - "查一下知识库"、"搜一下XXX"、"帮我回忆" → 检索记忆
  - "查看记忆统计"、"归档情况" → 查询状态

  触发场景（隐式 - AI语义自动检测）：
  - "总结"、"经验"、"教训"、"规则"、"方法" → 自动拆分存入（多卡片分类）
  - "方案"、"规划"、"计划"、"团队协作"、"复杂问题" → 自动触发检索
  - 提及"之前类似"、"有没有参考" → 自动检索相关经验
  
  核心功能：
  1. process_and_store() - 处理并存储记忆（自动LLM摘要+标签）
  2. search() - FTS全文检索（支持混合检索）
  3. 三层归档（热层0-6月/冷层6月-2年/冰层2-5年）
  4. 权限控制（私有/共享/公共）
  5. 检索日志与统计分析
  6. 无感存入 - 自动识别内容类型并拆分多卡片
---

# 第二大脑记忆系统

**版本**：V1.2  
**更新日期**：2026-03-30

---

## 系统定位

第二大脑记忆系统是个人长期知识存储与检索工具，核心是"记住你经历过的事"：
- 个人经历、对话总结、项目复盘
- 踩坑记录、经验教训、灵感
- 方法论，最佳实践

**不是**文档库，而是**记忆库**——存储"发生过的事"而非"死知识"。

---

## 架构概览

```
┌─────────────────────────────────────────────┐
│              KnowledgeSystem 主类              │
├─────────┬──────────┬─────────┬──────────────┤
│Database │LLM输出   │ FTS搜索 │ Archive管理  │
│(SQLite) │(摘要+标签)│(全文)   │(热/冷/冰)   │
├─────────┴──────────┴─────────┴──────────────┤
│         PermissionManager (私有/共享/公共)    │
└─────────────────────────────────────────────┘
```

**数据表**：
| 表 | 用途 | 说明 |
|----|------|------|
| `memories` | 记忆库 | 对话总结、复盘、教训 |
| `knowledge` | 知识库 | 规范化知识、教程，最佳实践 |
| `permissions` | 权限表 | 访问控制配置 |
| `retrieval_logs` | 检索日志 | 查询记录与分析 |
| `user_preferences` | 用户偏好 | 个性化配置 |
| `announcements` | 公告 | 系统通知 |

---

## 快速开始

### 初始化系统

```python
import os
import sys
sys.path.insert(0, 'E:/Users/ccb/.openclaw/workspace/knowledge-system')

from __init__ import KnowledgeSystem, get_knowledge_system

# 推荐方式：环境变量配置API密钥
api_key = os.environ.get('ZHIPU_API_KEY', '')
if not api_key:
    raise ValueError("请设置环境变量 ZHIPU_API_KEY")

# 方式1: 创建新实例
ks = KnowledgeSystem(
    db_path='./data/memory_db',  # SQLite数据库路径
    api_key=api_key
)

# 方式2: 获取全局单例
ks = get_knowledge_system(
    db_path='./data/memory_db',
    api_key=api_key
)
```

### 存储记忆（核心接口）

```python
import os
import time

# 带错误处理和重试的存储示例
def store_memory_with_retry(ks, message, max_retries=3, delay=1.0):
    """存储记忆，带重试机制"""
    for attempt in range(max_retries):
        try:
            result = ks.process_and_store(
                user_message=message,
                user_id="default",
                agent_id="main",
                context=None
            )
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"存储失败，{delay}秒后重试 ({attempt+1}/{max_retries}): {e}")
                time.sleep(delay)
            else:
                print(f"存储最终失败: {e}")
                raise

# 使用示例
result = store_memory_with_retry(ks, "今天完成了知识库测试，通过率98%")
print(f"重要性: {result['importance']}")       # high/medium/low
print(f"摘要: {result['text_summary']}")     # LLM生成的文本摘要
print(f"标签: {result['topic_tags']}")       # 自动生成的标签
print(f"已存储: {result['stored']}")          # True/False
print(f"记忆ID: {result.get('memory_id')}")   # 存储成功时有值
```

**存储决策规则**：
- `high` 重要性 → 必定存储
- `medium` 重要性 → 必定存储
- `low` 重要性 → 不存储（仅保留在会话上下文）

---

### 检索记忆（核心接口）

```python
# FTS全文检索
results = ks.search(
    query="知识库 测试 复盘",
    user_id="default",
    agent_id="main",
    search_type="fts",      # fts/vector/hybrid（当前用fts）
    top_k=5
)

for r in results:
    print(f"ID: {r['id']}")
    print(f"内容: {r['content'][:100]}")
    print(f"相关度: {r.get('score', 'N/A')}")
    print("---")
```

---

### 权限管理

```python
# 授权访问
ks.grant_access(agent_id="bravo", knowledge_id="mem_123", level="read")

# 撤销访问
ks.revoke_access(agent_id="bravo", knowledge_id="mem_123")

# 检查权限
has_access = ks.check_permission(agent_id="bravo", knowledge_id="mem_123")
```

---

### 统计分析

```python
stats = ks.get_stats()
print(f"记忆库: {stats['database']}")
print(f"归档层: {stats['archive']}")
```

---

## 三层归档机制

| 层级 | 条件 | 说明 |
|------|------|------|
| 热层 (hot) | 0-6个月 | 频繁访问，权重1.0 |
| 冷层 (cold) | 6个月-2年 | 较少访问，权重0.6 |
| 冰层 (ice) | 2-5年 | 基本不访问，权重0.4 |

**归档判断依据**：记忆创建时间 `created_at` 与当前时间差

**钢印机制**：`is_stamped=True` 的记忆永远不自动删除

---

## 检索日志

每次检索自动记录到 `retrieval_logs` 表，用于：
- 分析检索模式
- 评估检索质量
- 发现知识盲区

---

## 触发词参考

### 显式触发（明确说出发送词）

| 用户说 | 系统做 | 触发函数 |
|--------|--------|----------|
| "存入知识库" | 存储记忆 | `process_and_store()` |
| "记一下这个" | 存储记忆 | `process_and_store()` |
| "查一下知识库" | 检索记忆 | `search()` |
| "搜一下XXX" | 检索记忆 | `search()` |
| "查看统计" | 查询状态 | `get_stats()` |

### 隐式触发（AI语义自动检测，无需用户说出发送词）

| 用户说 | 系统做 | 触发机制 |
|--------|--------|----------|
| "总结一下今天的经验" | 自动拆分存入多张卡片 | 自动识别"总结"触发存储 |
| "这是个教训" | 自动存入教训类卡片 | 自动识别"教训"触发存储 |
| "正确做法是..." | 自动存入方法类卡片 | 自动识别"做法"触发存储 |
| "帮我规划一下" | 自动检索相关经验 | 自动识别"规划"触发检索 |
| "有没有类似方案" | 自动检索相关方案 | 自动识别"方案"触发检索 |
| "团队协作怎么做" | 自动检索团队协作经验 | 自动识别"团队协作"触发检索 |

---

## 数据库初始化

```bash
cd <your-workspace>/knowledge-system
python init_db.py
```

或使用Skill内置脚本：

```bash
cd <skill-dir>
python scripts/init_memory_db.py
```

首次使用需要初始化数据库，创建所有表结构。

---

## 配置说明

### 环境变量（必需）

```bash
# 设置API密钥（Windows PowerShell）
[System.Environment]::SetEnvironmentVariable("ZHIPU_API_KEY", "your-api-key", "User")

# Linux/Mac
export ZHIPU_API_KEY="your-api-key"
```

### 配置文件路径

- 数据库默认路径：`./data/memory_db`
- 测试数据库：`<your-workspace>/knowledge-system\data\memory_db`

---

## 目录结构

```
knowledge-system/
├── __init__.py              # 主类KnowledgeSystem（导入入口）
├── database.py             # 数据库操作
├── fts_search.py           # FTS全文搜索
├── retrieval.py             # 检索排序去重
├── permission.py           # 权限管理
├── archive.py              # 归档管理
├── llm_output.py          # LLM输出处理（生成摘要+标签）
├── init_db.py             # 数据库初始化
├── data/
│   └── memory_db           # SQLite数据库文件
└── tests/
```

---

## 运维指南

### 日常运维

```bash
# 1. 初始化数据库（如首次使用）
python scripts/init_memory_db.py

# 2. 查看记忆统计
python -c "
import sys
sys.path.insert(0, '.')
from __init__ import get_knowledge_system
ks = get_knowledge_system()
print(ks.get_stats())
"

# 3. 手动触发归档迁移
python -c "
import sys
sys.path.insert(0, '.')
from archive import get_archive_manager
am = get_archive_manager()
am.migrate_archive()
print('归档迁移完成')
"
```

### 备份与恢复

```bash
# 备份数据库
Copy-Item "<your-workspace>/knowledge-system\data\memory_db" `
         "E:\knowledge_base\backup\memory_db_$(Get-Date -Format 'yyyyMMdd')" -Recurse

# 恢复数据库
Copy-Item "E:\knowledge_base\backup\memory_db_20260329" `
         "<your-workspace>/knowledge-system\data\memory_db" -Recurse
```

### 日志查看

```bash
# 查看检索日志
sqlite3 data/memory_db "SELECT * FROM retrieval_logs ORDER BY created_at DESC LIMIT 10"

# 查看归档状态
sqlite3 data/memory_db "SELECT archive_level, COUNT(*) FROM memories GROUP BY archive_level"
```

---

## 安全说明

### API密钥传输安全

- API调用使用 **HTTPS**（TLS 1.2+ 加密传输）
- API密钥通过 Authorization: Bearer <token> 头部发送，全程加密
- 建议使用环境变量存储密钥，不要硬编码或写入配置文件

### SQL注入防护

- 所有数据库操作使用 **参数化查询**（? 占位符）
- SQLite本身具有SQL注入防护，但绝不使用字符串拼接构建SQL

### XSS防护

- 用户输入内容以**纯文本**形式存储，不执行任何HTML/代码
- 前端渲染时特殊字符自动转义（< → lt;，> → gt;）

---

## 注意事项

1. **FTS检索**：当前使用SQLite LIKE实现全文检索，无需额外模型
2. **向量搜索**：ChromaDB向量模块已集成但默认未启用（需要本地嵌入模型）
3. **LLM API**：必须配置API密钥才能生成摘要和标签，建议使用环境变量
4. **归档触发**：归档由定时任务或手动调用触发，非实时
5. **字段命名说明**：memories表中字段名为 vector_summary（LLM生成的文本摘要，非向量数据），兼容性已测试通过
6. **错误处理**：建议在生产环境使用带重试机制的存储函数

---

## 故障排查

### 存储失败

`
问题：store_memory_with_retry 报错 'API key not set'
解决：确认已设置环境变量 ZHIPU_API_KEY
命令：echo $ZHIPU_API_KEY  (Linux/Mac)
      echo %ZHIPU_API_KEY%  (Windows CMD)
`

### 检索无结果

`
问题：search() 返回空列表
排查步骤：
1. 确认数据库有数据：sqlite3 data/memory_db 'SELECT COUNT(*) FROM memories'
2. 确认查询词在内容中：使用更精确的关键词
3. 检查FTS索引是否正常
`

### 数据库初始化失败

`
问题：init_db.py 报错 'database is locked'
解决：关闭其他使用该数据库的连接，重试
`

### API调用超时

`
问题：process_and_store 超时
解决：检查网络到 open.bigmodel.cn 的连接
      或增加超时配置：timeout=60（秒）
`

---

## 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| V1.0 | 2026-03-29 | 初始版本，包含核心存储/检索/归档/权限功能 |
| V1.1 | 2026-03-29 | 修复P0问题2个（中等问题）+P1轻微3个+P2轻微2个，通过复审 |
| V1.2 | 2026-03-30 | 新增隐式触发词（AI语义自动检测）：总结/经验/教训/规则/方法/方案/规划/计划/团队协作/复杂问题 |

---

## 相关文档

- 详细设计：[references/DESIGN.md](references/DESIGN.md)
- API参考：[references/API.md](references/API.md)
- 测试方案：[references/TEST.md](references/TEST.md)

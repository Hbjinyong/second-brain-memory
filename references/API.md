# 第二大脑记忆系统 - API 参考

## KnowledgeSystem 主类

### `__init__(db_path, vector_dir, api_key)`

初始化知识系统实例。

**参数**：
- `db_path` (str): SQLite数据库路径，默认 `'./data/memory_db'`
- `vector_dir` (str): 向量数据库目录，默认 `None`
- `api_key` (str): LLM API密钥

---

### `process_and_store(user_message, user_id='default', agent_id=None, context=None)`

处理并存储记忆（核心接口）。

**参数**：
- `user_message` (str): 用户消息
- `user_id` (str): 用户ID，默认 `'default'`
- `agent_id` (str): Agent ID，默认 `None`
- `context` (str): 上下文信息，默认 `None`

**返回**：
```python
{
    'importance': 'high',        # high/medium/low
    'text_summary': '完成了知识库测试...',  # LLM摘要
    'topic_tags': ['测试', '知识库'],  # 标签列表
    'stored': True,              # 是否已存储
    'memory_id': 'mem_123'       # 存储成功时有值
}
```

**示例**：
```python
result = ks.process_and_store(
    user_message="今天完成了测试，通过率98%",
    user_id="default",
    agent_id="main"
)
if result['stored']:
    print(f"已存入记忆库，ID: {result['memory_id']}")
```

---

### `search(query, user_id='default', agent_id=None, search_type='fts', top_k=5)`

检索记忆（核心接口）。

**参数**：
- `query` (str): 查询词
- `user_id` (str): 用户ID，默认 `'default'`
- `agent_id` (str): Agent ID，默认 `None`
- `search_type` (str): 搜索类型，`'fts'` / `'vector'` / `'hybrid'`，默认 `'fts'`
- `top_k` (int): 返回结果数量，默认 `5`

**返回**：
```python
[
    {
        'id': 'mem_123',
        'content': '完整内容...',
        'created_at': '2026-03-29 10:00:00',
        'score': 0.85              # 相关度评分
    },
    ...
]
```

**示例**：
```python
results = ks.search("知识库 测试", top_k=10)
for r in results:
    print(f"{r['id']}: {r['content'][:50]}...")
```

---

### `check_permission(agent_id, knowledge_id, action='read')`

检查访问权限。

**参数**：
- `agent_id` (str): Agent ID
- `knowledge_id` (str): 知识/记忆ID
- `action` (str): 操作类型 `'read'` / `'write'` / `'admin'`，默认 `'read'`

**返回**：`bool` - 是否有权限

---

### `grant_access(agent_id, knowledge_id, level='read')`

授权访问。

**参数**：
- `agent_id` (str): Agent ID
- `knowledge_id` (str): 知识/记忆ID
- `level` (str): 权限级别 `'read'` / `'write'` / `'admin'`，默认 `'read'`

---

### `revoke_access(agent_id, knowledge_id)`

撤销访问权限。

**参数**：
- `agent_id` (str): Agent ID
- `knowledge_id` (str): 知识/记忆ID

---

### `get_stats()`

获取统计信息。

**返回**：
```python
{
    'database': {
        'memory_count': 2207,
        'knowledge_count': 2012,
        'permission_count': 6
    },
    'archive': {
        'hot': 623,
        'cold': 515,
        'ice': 968
    }
}
```

---

## Database 类

### `create_memory(...)`

创建记忆记录。

**参数**：
- `user_id` (str): 用户ID
- `content` (str): 内容
- `text_summary` (str): 摘要
- `topic_tags` (str): 标签（逗号分隔）
- `importance` (str): 重要性
- `agent_id` (str): Agent ID
- `is_stamped` (int): 是否钢印，默认 `0`

**返回**：`str` - 记忆ID

---

### `create_knowledge(...)`

创建知识记录。

**参数**：
- `user_id` (str): 用户ID
- `title` (str): 标题
- `description` (str): 描述
- `content` (str): 内容
- `topic` (str): 主题

**返回**：`int` - 知识ID

---

### `get_memories(user_id, archive_level=None, limit=100)`

获取记忆列表。

**参数**：
- `user_id` (str): 用户ID
- `archive_level` (str): 归档层级过滤，默认 `None`
- `limit` (int): 返回数量，默认 `100`

**返回**：`list` - 记忆列表

---

### `create_retrieval_log(...)`

创建检索日志。

**参数**：
- `query` (str): 查询词
- `returned_summary` (str): 返回结果摘要
- `result_count` (int): 结果数量
- `user_id` (str): 用户ID
- `agent_id` (str): Agent ID
- `case_type` (str): 查询类型

**返回**：`str` - 日志ID

---

## ArchiveManager 类

### `get_archive_stats()`

获取归档统计。

**返回**：
```python
{
    'hot': 623,
    'cold': 515,
    'ice': 968,
    'total': 2107
}
```

---

### `migrate_archive()`

执行归档迁移（热→冷→冰）。

---

### `cleanup_archives()`

清理超过保留期限的记忆。

---

## FTSSearch 类

### `search(query, top_k=5)`

FTS全文搜索。

**参数**：
- `query` (str): 查询词
- `top_k` (int): 返回数量

**返回**：`list` - 搜索结果

---

## 全局函数

### `get_knowledge_system(db_path=None, vector_dir=None, api_key=None)`

获取全局单例实例。

**参数**：同 `KnowledgeSystem.__init__`

**返回**：`KnowledgeSystem` 实例

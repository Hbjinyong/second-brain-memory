# 第二大脑记忆系统 - 详细设计

## 一、设计目标

### 1.1 核心问题
- 对话信息随上下文消失，无法长期记忆
- 重要经验难以回溯
- 知识碎片化，无法系统化管理

### 1.2 解决方案
构建"第二大脑"记忆系统，核心是记住"经历过的事"：
- 自动重要性判断，只存储值得记住的
- 自动摘要和标签，便于检索
- 三层归档，热数据高效访问，冷数据节省资源
- 权限控制，保护敏感记忆

## 二、系统架构

### 2.1 模块划分

```
KnowledgeSystem (主类)
├── Database (数据库操作)
├── LLMOutput (LLM输出处理)
├── FTSSearch (全文搜索)
├── VectorSearch (向量搜索) [备用]
├── PermissionManager (权限管理)
├── RetrievalRanker (检索排序)
└── ArchiveManager (归档管理)
```

### 2.2 数据模型

#### memories 表（记忆库）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 主键，格式: mem_{timestamp} |
| user_id | TEXT | 用户ID |
| agent_id | TEXT | Agent ID |
| content | TEXT | 原始内容 |
| text_summary | TEXT | LLM生成的向量摘要 |
| tags | TEXT | JSON格式标签数组 |
| importance | TEXT | high/medium/low |
| archive_level | TEXT | hot/cold/ice/stamped |
| is_stamped | INTEGER | 是否钢印（永不自动删除） |
| query_freq | INTEGER | 查询频次 |
| weight | REAL | 权重（影响排序） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### knowledge 表（知识库）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键自增 |
| user_id | TEXT | 用户ID |
| title | TEXT | 标题 |
| description | TEXT | 简短描述 |
| content | TEXT | 详细内容 |
| topic | TEXT | 主题分类 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### permissions 表（权限）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键自增 |
| agent_id | TEXT | Agent ID |
| knowledge_id | TEXT | 知识/记忆ID |
| permission | TEXT | read/write/admin |
| created_at | TEXT | 创建时间 |

#### retrieval_logs 表（检索日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 主键 |
| query | TEXT | 查询词 |
| returned_summary | TEXT | 返回结果摘要 |
| quality_score | REAL | 质量评分 |
| user_feedback | TEXT | 用户反馈 |
| cleaned | INTEGER | 是否已清洗 |
| case_type | TEXT | 查询类型 |
| created_at | TEXT | 创建时间 |

## 三、核心流程

### 3.1 存储流程（process_and_store）

```
用户消息
    ↓
LLM重要性判断（high/medium/low）
    ↓
importance in [high, medium]? → No → 不存储，仅会话内保留
    ↓ Yes
LLM生成摘要 + 标签
    ↓
存入memories表
    ↓
存入向量库（如启用）
    ↓
返回存储结果
```

### 3.2 检索流程（search）

```
用户查询
    ↓
FTS全文搜索（title LIKE OR content LIKE）
    ↓
向量搜索（如启用）
    ↓
混合结果去重（Jaccard相似度）
    ↓
综合排序（相关性 × 权重 × 时间衰减）
    ↓
返回Top-K结果
    ↓
记录检索日志
```

### 3.3 归档流程

```
定时任务扫描
    ↓
memories表按created_at计算年龄
    ↓
年龄 6-12月 → hot → cold
年龄 12-24月 → cold → ice
年龄 >60月 → 触发删除提醒
    ↓
更新archive_level字段
```

## 四、LLM输出处理

### 4.1 输入处理

```python
def process_input(user_message, context=None):
    # 构造prompt
    prompt = f"""分析以下用户消息，判断其重要性：
    
用户消息：{user_message}

判断标准：
- high: 重要决策、关键问题、踩坑记录、经验教训
- medium: 有价值的信息、项目进展、学习心得
- low: 日常闲聊、一般性询问

同时生成：
1. 一句话摘要（不超过50字）
2. 3-5个标签（JSON数组格式）

输出格式：
 importance: [high/medium/low]
 summary: [一句话摘要]
 tags: [标签数组]
"""
    # 调用LLM
    response = llm.chat(prompt)
    # 解析结果
    return parse_response(response)
```

### 4.2 摘要生成

摘要用于快速判断记忆内容，无需查看完整内容。

**要求**：
- 不超过50字
- 包含核心信息
- 保留关键细节（数字、名词、动作）

## 五、检索排序算法

### 5.1 综合评分公式

```
final_score = relevance × 0.5 + time_decay × 0.3 + weight × 0.2
```

### 5.2 时间衰减

```python
days_old = (now - created_at).days
time_decay = max(0, 1 - days_old / 365)
```

### 5.3 去重算法（Jaccard相似度）

```python
def jaccard_similarity(text1, text2):
    set1, set2 = set(text1.lower()), set(text2.lower())
    return len(set1 & set2) / len(set1 | set2)

# 阈值0.85以上视为重复
```

## 六、权限模型

### 6.1 权限类型

| 类型 | 说明 |
|------|------|
| private | 仅所有者可访问 |
| shared | 指定Agent可访问 |
| public | 所有Agent可访问 |

### 6.2 权限检查流程

```python
def check_access(agent_id, knowledge_id):
    # 1. 检查是否是public
    # 2. 检查是否是所有者
    # 3. 检查是否有shared授权
    # 4. 都不满足 → 拒绝访问
```

## 七、三层归档设计

### 7.1 分层标准

| 层级 | 年龄范围 | 访问频率 | 权重 | 自动清理 |
|------|----------|----------|------|----------|
| hot | 0-6月 | 高 | 1.0 | 否 |
| cold | 6月-2年 | 低 | 0.6 | 否 |
| ice | 2-5年 | 极低 | 0.4 | 否（触发提醒） |
| stamped | 任意 | - | 1.0 | 否（钢印保护） |

### 7.2 归档迁移

- 热→冷：满6个月自动迁移
- 冷→冰：满2年自动迁移
- 删除提醒：满5年触发通知

## 八、配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| TRAIN_WINDOW | 6 | 训练窗口（月） |
| TOP_N | 25 | 持仓数量 |
| WEIGHT_HOT | 1.0 | 热层权重 |
| WEIGHT_COLD | 0.6 | 冷层权重 |
| WEIGHT_ICE | 0.4 | 冰层权重 |
| RETENTION_YEARS | 5 | 保留年限 |
| STAMPED_PROTECTION | True | 钢印保护 |

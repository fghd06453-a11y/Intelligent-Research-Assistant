# Intelligent Research System

> 一个基于 **FastAPI + LangGraph + Vue 3 + RAG + 多智能体工作流** 的智能研究助手。系统可以根据用户问题自动选择“快速回答”或“深度研究”路径，并完成任务拆解、网络检索、本地知识库检索、证据裁判、分析总结和 Markdown 报告生成。

## 项目简介

Intelligent Research System 是一个面向研究、分析和知识问答场景的多智能体系统。用户在前端输入问题后，后端会通过 FastAPI 接收请求，并交给 LangGraph 编排的多智能体工作流处理。

系统主要支持两类路径：

- **快速回答**：适合问候、闲聊、简单常识问答。
- **深度研究**：适合调研、对比、趋势分析、报告生成、多来源证据整合等复杂任务。

深度研究路径会自动完成：

1. 判断用户问题意图。
2. 拆解研究目标和子问题。
3. 调用 Web 搜索获取外部资料。
4. 调用本地 RAG 检索企业或个人知识库。
5. 对证据进行评分、去重、冲突审计。
6. 判断信息是否充足，必要时自动补搜。
7. 输出带来源引用的 Markdown 研究报告。
8. 保存短期对话和长期记忆。

## 核心能力

- **多智能体编排**：基于 LangGraph 将意图识别、规划、检索、证据裁判、分析、反思、写作拆成独立节点。
- **快速 / 深度双路径**：简单问题直接回答，复杂问题进入完整研究链路。
- **Web + Local 双源检索**：同时支持 Bocha Web Search 和 Milvus 本地向量知识库。
- **证据驱动输出**：通过 `source_id` 管理来源，降低模型编造引用的风险。
- **SSE 流式响应**：前端可实时展示“正在规划 / 正在检索 / 正在分析 / 正在写作”等进度。
- **会话记忆增强**：支持短期对话、长期用户画像、偏好和历史任务记忆。
- **可降级存储设计**：Checkpointer 优先 PostgreSQL，其次 Redis，最后内存。

## 技术栈

### 后端

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic / pydantic-settings
- LangGraph
- LangChain
- DashScope / Qwen
- PostgreSQL
- Redis，可选
- Milvus
- Bocha Web Search API

### 前端

- Vue 3
- TypeScript
- Vite
- Fetch + ReadableStream 解析 SSE

### 基础设施

- Docker Compose
- PostgreSQL
- Milvus Standalone
- etcd
- MinIO
- Attu

## 项目结构

```text
.
├── app
│   ├── app_main.py                         # FastAPI 后端启动入口
│   ├── backend
│   │   ├── config
│   │   │   └── settings.py                  # Web 服务配置
│   │   ├── router
│   │   │   ├── health_router.py             # 健康检查接口
│   │   │   └── research_router.py           # 研究接口：run / stream
│   │   ├── schemas
│   │   │   ├── health.py                    # 健康检查响应模型
│   │   │   └── research.py                  # 研究请求/响应模型
│   │   └── service
│   │       └── workflow_service.py          # FastAPI 与 LangGraph 的桥接层
│   └── mult_agents
│       ├── config.py                        # 多智能体运行配置
│       ├── graph.py                         # LangGraph 工作流图
│       ├── main.py                          # Agent、MemoryManager、Checkpointer 工厂
│       ├── nodes.py                         # 各工作流节点实现
│       ├── prompts.py                       # 各 Agent 的系统提示词
│       ├── tools.py                         # Web 搜索、本地 RAG 和辅助工具
│       ├── memory                           # 短期/长期记忆系统
│       └── rag                              # Milvus RAG 检索与入库逻辑
├── front
│   └── agent_front
│       ├── src
│       │   ├── main.ts                      # Vue 前端入口
│       │   └── App.vue                      # 主页面和流式请求逻辑
│       ├── package.json
│       └── vite.config.ts                   # 前端代理配置
├── docker-compose.yml                       # PostgreSQL / Milvus / MinIO / etcd / Attu
├── requirements.txt                         # Python 依赖
├── pyproject.toml                           # Python 项目元信息
├── .env.template                            # 环境变量模板
└── README.md
```

## 整体执行流程

一次典型的深度研究请求会经过下面这条链路：

```text
浏览器输入问题
  -> Vue App.vue::runResearch()
  -> POST /api/v1/research/stream
  -> FastAPI research_router.stream_research()
  -> WorkflowService.stream_events()
  -> 后台线程运行 LangGraph app.stream()
  -> intent_node：判断快速回答还是深度研究
  -> plan_node：拆解问题并生成搜索计划
  -> web_search_node：调用 Bocha 搜索网络证据
  -> local_rag_node：调用 Milvus 检索本地知识库
  -> deep_dive_node：证据评分、去重、冲突审计
  -> analyze_node：生成分析结论并判断是否需要补搜
  -> reflect_node：如证据不足，生成补搜计划并循环
  -> write_node：生成最终 Markdown 研究报告
  -> MemoryManager.persist_turn()：保存本轮对话和记忆
  -> SSE final event 返回前端
  -> Vue 页面展示最终报告
```

如果问题被识别为简单问题，则执行更短路径：

```text
intent_node -> direct_answer_node -> END
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/fghd06453-a11y/intelligent-research-system.git
cd intelligent-research-system
```

### 2. 准备环境变量

复制环境变量模板：

```bash
cp .env.template .env
```

然后根据实际情况填写：

```env
DASHSCOPE_API_KEY=你的阿里云百炼Key
BOCHA_API_KEY=你的博查搜索Key
MODEL=qwen-plus

POSTGRES_DSN=postgresql://用户名:密码@127.0.0.1:5432/数据库名
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
MILVUS_COLLECTION=mult_agent_memory

ENABLE_MEMORY=true
SHORT_TERM_BACKEND=postgres
LONG_TERM_BACKEND=postgres
CHECKPOINTER_BACKEND=postgres
ENABLE_MILVUS=true

TENANT_ID=default_tenant
USER_ID=default_user
THREAD_ID=default
MAX_ITERATIONS=3
```

> 注意：不要把真实 `.env` 文件提交到公开仓库。

### 3. 启动基础设施

项目提供了 Docker Compose，用于启动 PostgreSQL、Milvus、etcd、MinIO 和 Attu：

```bash
docker compose up -d
```

常用端口：

| 服务 | 默认端口 | 说明 |
|---|---:|---|
| PostgreSQL | 5432 | 记忆、checkpoint 等数据存储 |
| Milvus | 19530 | 向量检索服务 |
| MinIO | 9000 / 9001 | Milvus 对象存储依赖 |
| Attu | 8080 | Milvus Web 管理界面 |

### 4. 安装后端依赖

建议使用虚拟环境：

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

如果使用 PowerShell，可执行：

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5. 启动后端

推荐在 `app` 目录下启动：

```bash
cd app
python app_main.py
```

后端默认运行在：

```text
http://127.0.0.1:8000
```

健康检查：

```text
GET http://127.0.0.1:8000/health
```

### 6. 启动前端

打开另一个终端：

```bash
cd front/agent_front
npm install
npm run dev
```

前端默认运行在：

```text
http://127.0.0.1:5173
```

Vite 会把 `/api` 和 `/health` 请求代理到后端 `http://127.0.0.1:8000`。

## API 说明

### 健康检查

```http
GET /health
```

响应示例：

```json
{
  "status": "ok",
  "service": "research-system-backend"
}
```

### 同步研究接口

```http
POST /api/v1/research/run
Content-Type: application/json
```

请求体：

```json
{
  "query": "帮我调研企业级 AI Agent 的落地趋势",
  "user_id": "user01",
  "thread_id": "thread01",
  "tenant_id": "default_tenant",
  "max_iterations": 3,
  "enable_memory": true
}
```

响应体：

```json
{
  "query": "帮我调研企业级 AI Agent 的落地趋势",
  "user_id": "user01",
  "thread_id": "thread01",
  "tenant_id": "default_tenant",
  "final": "最终研究报告正文..."
}
```

### 流式研究接口

```http
POST /api/v1/research/stream
Content-Type: application/json
```

该接口返回 `text/event-stream`，前端会持续收到如下事件：

```text
data: {"type":"status","message":"任务已接收，正在初始化多智能体链路"}

data: {"type":"phase","node":"plan","message":"Planner 正在拆解问题"}

data: {"type":"phase","node":"web_search","message":"Web Scout 正在检索网络证据"}

data: {"type":"final","final":"最终 Markdown 报告..."}
```

## 核心工作流节点

| 节点 | 职责 | 输出重点 |
|---|---|---|
| `intent` | 判断问题走快速回答还是深度研究 | `intent` |
| `direct_answer` | 简单问题直接回答 | `final` |
| `plan` | 拆解目标、子问题和搜索计划 | `plan`, `sub_questions`, `search_plan` |
| `web_search` | 调用 Web 搜索并整理网页证据 | `web_evidence` |
| `local_rag` | 检索本地 Milvus 知识库 | `local_evidence` |
| `deep_dive` | 证据评分、去重、冲突审计 | `evidence_pool`, `source_index`, `audit_flags` |
| `analyze` | 形成分析结论，判断是否需要补搜 | `findings`, `needs_more_research`, `missing_gaps` |
| `reflect` | 生成补搜查询并进入下一轮检索 | `supplementary_queries`, `iteration` |
| `write` | 生成最终 Markdown 研究报告 | `final` |

## 重要概念

### `thread_id` 不是任务 ID

当前系统没有传统后台任务队列，也没有 `task_id`、任务状态查询接口或取消接口。`thread_id` 主要用于：

- 区分会话线程；
- 关联短期记忆；
- 关联 LangGraph checkpoint；
- 让多轮对话保持上下文。

### Memory、RAG、Checkpointer 的区别

| 模块 | 作用 | 典型存储 |
|---|---|---|
| MemoryManager | 用户画像、短期对话、长期偏好和历史任务 | PostgreSQL / Redis / SQLite / Milvus |
| RAG | 检索本地知识库内容 | Milvus |
| Checkpointer | 保存 LangGraph 节点执行状态 | PostgreSQL / Redis / 内存 |

### 为什么要有 `source_id`

系统会给 Web 和 Local 检索结果分配来源 ID，例如：

```text
WEB1_1-1
LOC1_1-3
```

后续证据裁判、分析和写作都必须基于这些合法来源 ID。这样可以减少模型编造来源，便于最终报告追踪证据。

## 本地知识库入库

本地知识库检索依赖 Milvus。入库逻辑位于：

```text
app/mult_agents/rag/ingest.py
```

当前脚本中的 `INPUT_PATH`、`COLLECTION_NAME` 等常量需要根据实际情况配置后再运行。入库流程大致为：

1. 收集 `.txt`、`.md`、`.markdown` 文件。
2. 使用文本切分器切成 chunk。
3. 使用 DashScope Embedding 生成向量。
4. 写入 Milvus collection。
5. 在线研究时由 `local_rag_node` 检索相似内容。

## 开发者阅读路线

如果你想快速读懂项目，建议按以下顺序阅读源码：

1. `app/app_main.py`：后端启动入口。
2. `app/backend/router/research_router.py`：HTTP API 入口。
3. `app/backend/service/workflow_service.py`：FastAPI 与 LangGraph 的桥梁。
4. `app/mult_agents/config.py`：多智能体配置来源。
5. `app/mult_agents/main.py`：Agent、MemoryManager、Checkpointer 初始化。
6. `app/mult_agents/state.py`：工作流共享状态结构。
7. `app/mult_agents/graph.py`：LangGraph 节点和边。
8. `app/mult_agents/nodes.py`：每个节点的具体执行逻辑。
9. `app/mult_agents/tools.py`：Web 搜索和 RAG 工具。
10. `app/mult_agents/memory/manager.py`：记忆系统总入口。
11. `front/agent_front/src/App.vue`：前端如何发起流式请求并展示结果。

## 常见问题

### 第一次请求为什么比较慢？

第一次请求会触发 `WorkflowService._ensure_initialized()`，它会初始化配置、记忆管理器、Agent、Checkpointer 和 LangGraph app，所以耗时会比后续请求更长。

### 为什么前端用 `/api/v1/research/stream`？

深度研究可能耗时较长，流式接口可以实时返回阶段进度，用户体验比等待同步响应更好。

### 如果没有配置 Bocha API Key 会怎样？

Web 搜索会跳过，系统仍会尝试使用本地 RAG 和已有上下文，但外部证据会不足。

### 如果 Milvus 没有数据会怎样？

本地知识库检索会返回空结果。系统仍可依赖 Web 搜索完成研究，但本地知识增强能力不可用。

### 是否支持取消任务？

当前版本没有独立的任务取消接口。流式请求断开后，后端工作线程可能仍会继续执行到结束。

## 许可证

当前仓库尚未声明许可证。若准备开源发布，建议补充 `LICENSE` 文件。

## 致谢

本项目基于 FastAPI、Vue、LangGraph、LangChain、Milvus、DashScope 等开源或云服务生态构建，适合作为多智能体研究系统、RAG 应用和后端工作流编排的学习与实践项目。

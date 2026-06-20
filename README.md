# 智能面试系统 (AI Interview Platform)

基于 **多 Agent + LangChain + FastAPI + Vue 3 + PostgreSQL** 的企业级智能面试项目。
管理员录入面试者与岗位信息后系统自动生成登录账号；面试者登录后通过 WebSocket 实时答题，
全流程由 6 个职责单一的 AI Agent 协作完成：出题、质检、记录、评分、分析、总结建议。

> 适合作为企业面试 / 课程设计 / 简历项目展示。

---

## ✨ 核心功能

### 管理员（admin）
- 添加面试者：填写姓名、**面试岗位**、**岗位所需技术（标签）**、级别、题目数量等
- 提交后**自动生成登录账号 + 随机密码**（明文仅展示一次），发给面试者
- 查看面试者列表、重置密码
- 查看每位面试者的 AI 评估报告（综合分、优缺点、知识点掌握度、各题评分、录用建议）

### 面试者（candidate）
- 用管理员发的账号登录
- 进入答题间，**WebSocket 实时问答**：逐句作答，每句话都会被实时记录
- 答完自动评分并进入下一题，全部完成后生成报告
- 查看自己的面试报告

---

## 🤖 多 Agent 架构

| Agent | 职责 | 触发时机 | 文件 |
|------|------|---------|------|
| **题库生成 Agent** | 根据岗位+技术点生成面试题 | 管理员添加面试者后（后台任务） | `agents/question_generator.py` |
| **题目质检 Agent** | 对每道题打质量分，过滤不合格题目 | 紧随生成之后 | `agents/quality_checker.py` |
| **记录 Agent** | 把候选人零散口语整理成连贯 Q&A 文本 | 每题作答完毕 | `agents/recorder.py` |
| **评分 Agent** | 从正确性/完整性/深度/表达多维度打分 | 每题作答完毕 | `agents/scorer.py` |
| **分析 Agent** | 梳理优缺点 + 各技术点掌握度 | 全部答完 | `agents/analyst.py` |
| **总结 Agent** | 总体评价 + 录用建议 | 全部答完 | `agents/summary.py` |

> 说明：**逐句实时记录**本身不需要 LLM（在 `ws.py` 中直接落库 `QARecord`），
> 记录 Agent 仅负责单题结束时的整理润色——符合“这个也可以不要 agent”的需求。

编排逻辑见 `backend/app/services/interview_service.py`。

---

## 🗂 目录结构

```
interview-project/
├── docker-compose.yml          # 一键启动 PostgreSQL + 后端
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── app/
│       ├── main.py             # FastAPI 入口（建表 + 初始化 admin）
│       ├── config.py           # 配置
│       ├── database.py         # async SQLAlchemy
│       ├── models.py           # 数据模型
│       ├── schemas.py          # Pydantic
│       ├── security.py         # JWT / 密码 / 账号生成
│       ├── deps.py             # 认证依赖 & 角色校验
│       ├── agents/             # 6 个 Agent
│       ├── services/           # 多 Agent 编排
│       └── routers/            # auth / admin / interview / ws
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── views/              # Login / AdminDashboard / InterviewRoom / 报告
        ├── components/ReportView.vue
        ├── router.js  api.js  style.css
```

---

## 🚀 快速开始

### 方式一：Docker（推荐，含 PostgreSQL）

```bash
# 1. 在项目根目录创建 .env（供 docker-compose 读取）
cat > .env <<'EOF'
OPENAI_API_KEY=sk-你的key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
SECRET_KEY=请改成一段随机长字符串
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
EOF

# 2. 启动数据库 + 后端
docker compose up --build
# 后端: http://localhost:8002  （文档 http://localhost:8002/docs）

# 3. 另开终端启动前端
cd frontend
npm install
npm run dev
# 前端: http://localhost:5173
```

### 方式二：本地开发（后端用本机 PostgreSQL）

```bash
# 后端
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env        # 填入 OPENAI_API_KEY、数据库地址
uvicorn app.main:app --reload

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

---

## 🧭 使用流程

1. 浏览器打开 `http://localhost:5173`
2. 用 **admin / admin123** 登录管理后台
3. 「添加面试者」填写姓名、岗位、所需技术等 → 提交，记下生成的**账号/密码**
4. 等待几秒（AI 后台出题 + 质检）
5. 退出，用面试者账号登录 → 进入答题间，逐句作答、提交
6. 答完后系统自动评分并生成报告
7. 面试者可看「我的报告」；管理员可在列表「查看报告」

---

## ⚙️ 配置项（backend/.env）

| 变量 | 说明 | 默认 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 异步连接串 | `postgresql+asyncpg://interview:interview@localhost:5432/interview` |
| `OPENAI_API_KEY` | OpenAI 密钥 | 必填 |
| `OPENAI_BASE_URL` | API 地址（可指向兼容网关） | OpenAI 官方 |
| `LLM_MODEL` | 模型名 | `gpt-4o-mini` |
| `SECRET_KEY` | JWT 签名密钥 | 必改 |
| `ADMIN_USERNAME/PASSWORD` | 初始管理员 | admin / admin123 |

---

## 🔌 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录（OAuth2 表单） |
| POST | `/api/admin/candidates` | 添加面试者，返回账号密码 |
| GET | `/api/admin/candidates` | 面试者列表 |
| GET | `/api/admin/interviews/{id}/report` | 查看报告 |
| GET | `/api/interview/my` | 面试者查看自己的面试 |
| GET | `/api/interview/my/report` | 面试者查看报告 |
| WS | `/ws/interview?token=JWT` | 实时答题 |

完整交互文档：`http://localhost:8002/docs`

---

## 📝 技术栈

- **后端**：FastAPI · SQLAlchemy 2 (async) · asyncpg · LangChain · langchain-openai · python-jose · passlib
- **前端**：Vue 3 · Vite · Vue Router · Pinia · Axios · 原生 WebSocket
- **数据库**：PostgreSQL 16
- **部署**：Docker Compose

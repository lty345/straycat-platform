# 流浪猫内容平台（后端 · 开发中）

给流浪猫做的一个内容社区：看猫、读救助故事、了解养猫知识，从里面获得一点治愈。
技术重点不是"又多一个 CRUD"，而是 **个性化推荐**：先靠埋点积累行为，再用可解释的规则排序。

> ⚠️ 当前状态：**只有地基**（基础设施已就绪，业务代码未开始）。
> 开发边界见 [`docs/MVP-边界.md`](docs/MVP-边界.md) —— 先看那个，再动手。

## 技术栈

| 分类 | 选型 |
|---|---|
| Web 框架 | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.x 异步 + aiomysql |
| 数据库 | MySQL 8.0 |
| 日志 | loguru 双文件按天轮转 + ContextVar 传 traceid |
| 测试 | pytest + pytest-asyncio（ASGI 进程内，不占端口） |
| 包管理 | uv |

## 快速开始

```bash
# 1. 装依赖
uv sync

# 2. 配置（DATABASE + SECRET_KEY）
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # 生成 SECRET_KEY

# 3. 建库（先建库，再建表）
#    mysql -uroot -p -e "CREATE DATABASE straycat CHARACTER SET utf8mb4;"
uv run python main.py

# 4. 启动（dev 带热重载；run 不带）
uv run fastapi dev app.py
```

打开 http://127.0.0.1:8000/docs 看接口文档，`GET /health` 验证服务活着。

## 测试

```bash
uv run pytest -q
```

前置条件：MySQL 开着、`.env` 存在（`lifespan` 会 `SELECT 1`）。

## 目录约定

```
app.py                  入口：日志 → app → 中间件 → 异常处理器 → 路由
config/                 配置（全部从 .env 注入，代码里不留密码）
db/
  database.py           异步引擎 / 会话工厂 / 会话依赖
  model/                每个表一个文件
exts/
  exceptions/           业务异常 + 4 类全局异常处理器
  responses/            统一响应封装
  logururoute/          loguru 配置
  requestvar/           ContextVar，存放 traceid / request
  schemas/page.py       通用分页容器 Page[T]
middlewares/loger/      traceid 日志中间件
apis/<模块>/             api / schemas / repository / dependencies
services/               跨表业务编排（抢占、推荐打分）
tests/                  conftest.py 提供 session 级 client
docs/                   设计文档（MVP 边界、推荐算法说明）
```

**分层判断法**：知道 HTTP 的放 `apis/*/api/`，知道 SQL 的放 `apis/*/repository/`，只做业务判断的两者都不放的放 `services/`。

## 待办

- [ ] 三张核心表：`cat` / `content` / `user_event`
- [ ] 内容列表 + 详情 + 分页
- [ ] 埋点接口（浏览 / 点赞）
- [ ] 规则版推荐（标签匹配 + 时间衰减 + 热门兜底）
- [ ] 领养申请（一只猫只能被一人申请 → 原子抢占 + 唯一约束）
- [ ] pytest 覆盖：分页 / 埋点 / 推荐排序 / 抢占

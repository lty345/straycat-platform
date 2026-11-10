# 流浪猫内容平台（后端 + 前端，开发中）

给流浪猫做的一个内容社区：看猫、读救助故事、了解养猫知识。
技术重点不是"又一套 CRUD"，而是 **个性化推荐**：先靠埋点积累行为，再用可解释的规则排序。

> **当前状态**：内容这条垂直切片已打通（建表 → 分页接口 → 前端列表/详情）。
> 埋点、推荐、领养抢占还是待办，见文末。
> 开发边界见 [`docs/MVP-边界.md`](docs/MVP-边界.md)，个人方向决策见 [`docs/方向决策表.md`](docs/方向决策表.md)。

## 技术栈

| 分类 | 选型 |
|---|---|
| Web 框架 | FastAPI + Pydantic v2 |
| ORM | SQLAlchemy 2.x 异步 + aiomysql |
| 数据库 | MySQL 8.0 |
| 日志 | loguru 双文件按天轮转 + ContextVar 传 traceid |
| 测试 | pytest + pytest-asyncio（ASGI 进程内，不占端口） |
| 前端 | Vue 3 + Vite + vue-router + axios |
| 包管理 | uv（后端）/ npm（前端） |

## 快速开始

```bash
# 1. 装依赖
uv sync

# 2. 配置（DATABASE + SECRET_KEY）
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # 生成 SECRET_KEY

# 3. 建库 + 建表（先建库，再建表）
#    mysql -uroot -p -e "CREATE DATABASE straycat CHARACTER SET utf8mb4;"
uv run python main.py

# 4. 造 20 条种子数据（可重复运行，幂等）
uv run python scripts/seed_content.py

# 5. 起后端（dev 带热重载）
uv run fastapi dev app.py        # http://127.0.0.1:8000/docs

# 6. 起前端（另开一个终端，后端要先起）
cd web && npm install && npm run dev   # http://localhost:5173
```

## 已实现的接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/api/v1/contents` | 内容列表，分页 + 筛选 |
| GET | `/api/v1/contents/{id}` | 内容详情（含正文） |

**列表参数**：`page`（≥1）、`page_size`（1~100）、`mood`（治愈/科普/揪心/欢乐）、`keyword`（匹配标题/摘要/标签）
**列表返回**：`{ list, total, page, page_size }`，列表项**不含 body**

**统一响应**是 `{ success, code, api_code, message, result, timestamp }`：
`code` 是 HTTP 状态码，`api_code` 是业务码。业务失败也返回 HTTP 200，前端只判 `success`。

| 场景 | HTTP | api_code |
|---|---|---|
| 正常 | 200 | 200 |
| 内容不存在 | **200** | **30001** |
| 参数不合法（page=0 等） | 400 | 400 |
| 路由不存在 | 404 | 404 |
| 服务端异常 | 500 | 500 |

## 目录约定

```
app.py                  入口：日志 → app → 中间件 → 异常处理器 → 路由
config/                 配置（全部从 .env 注入）
db/
  database.py           异步引擎 / 会话工厂 / 会话依赖
  model/                每个表一个文件
exts/
  exceptions/           业务异常 + 4 类全局异常处理器
  responses/            统一响应封装 + 自定义 JSON 编码器
  logururoute/          loguru 配置（控制台 + info/error 双文件）
  requestvar/           ContextVar，存放 traceid / request
  schemas/page.py       通用分页容器 Page[T]
middlewares/loger/      traceid 日志中间件
apis/content/           api（HTTP）/ schemas（出入参）/ repository（SQL）
services/               跨表业务编排（推荐打分、领养抢占；还是空的）
tests/                  pytest，conftest 提供 session 级 client
docs/                   MVP 边界、表结构、方向决策
web/                    Vue 3 前端（列表页 + 详情页）
```

**分层判断法**：知道 HTTP 的放 `apis/*/api/`，知道 SQL 的放 `apis/*/repository/`，只做业务判断的两者都不放的放 `services/`。

## 几个值得说的实现细节

1. **分页必须显式排序**：`ORDER BY pub_time DESC, id DESC`。`pub_time` 精度是秒、批量导入会有大量同秒记录，只按时间排会让 `offset/limit` 翻页出现重复或漏条（page drift）。第二排序键 `id` 保证并列时顺序确定。
2. **列表不返回正文**：`ContentListOut` 里没有 `body` 字段，查询层再 `defer(Content.body)`。这是双层保险——列表接口一旦能返正文，详情接口就会被绕过，正文的懒加载策略也就失效了。
3. **`list` 和 `count` 共用一套 where**：`_apply_filters()` 被两个函数复用，保证 `total` 和实际能翻到的条数一致（否则分页条会算出"共 5 页但第 2 页是空的"）。
4. **查不到是业务异常，不是空数据**：repository 返回 `None`（只回答"库里有没有"），"内容不存在 → 30001"由 api 层抛 `BusinessError` 决定。
5. **traceid 日志链路**：中间件生成 traceid → 存进 ContextVar → 日志函数自动带上 → 响应头回传 `X-Trace-Id`，报错时用户能直接把 id 报给你。

## 测试

```bash
uv run pytest -q
```

前置条件：MySQL 开着、`.env` 存在。
`tests/test_content.py` 用自建夹具（插 3 条 → 测 → 删），不依赖种子数据，覆盖：分页边界、列表不带 body、倒序、详情、404 业务码、参数校验。

## 待办

- [ ] `cat` / `user_event` / `app_user` 三张表
- [ ] 埋点接口（浏览 / 点赞）
- [ ] 规则版推荐 `GET /feed`：标签匹配 + 情绪偏好 + 同城 + 热度，再乘时间衰减 `0.5^(天数/7)`
- [ ] 领养申请：`UPDATE ... WHERE id=? AND status='待领养'` + 判断 rowcount（并发 10 个只成功 1 个）
- [ ] 前端：mood/关键词筛选 UI、列表页样式收尾
- [ ] README 补一节"推荐分数怎么算、为什么这么定权重"（等 `/feed` 做完）

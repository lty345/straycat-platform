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

# 4. 造种子数据（都可重复运行，幂等）
uv run python scripts/seed_content.py          # 24 条内容（含长文与封面）
uv run python scripts/seed_users_events.py     # 3 个用户 + 50 条埋点（含冷启动样本）

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
| POST | `/api/v1/events` | 写一条埋点（view / like） |
| GET | `/api/v1/users/{id}/events` | 按用户查埋点，可分页/按类型过滤 |
| GET | `/api/v1/feed` | **个性化推荐流**（`user_id` + 分页） |

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

## 推荐算法：分数怎么算，为什么这么定权重

这是本项目唯一不是 CRUD 的部分。规则版推荐，**每一项都能说出"为什么这条排前面"**。

```
score = (3 × 标签匹配数
       + 2 × 情绪偏好匹配
       + 1 × 同城
       + 0.5 × 热度)  ×  0.5 ** (已发布天数 / 7)
```

### 四项怎么算

| 项 | 权重 | 算法 | 为什么是这个权重 |
|---|---|---|---|
| **标签匹配** | **3** | `user.interest_tags ∩ content.tags` 的个数 | 两个**确定**信号相交：用户主动声明的兴趣 × 内容明确标注的标签。最针对个人，权重最高 |
| **情绪偏好** | **2** | `content.mood == 用户历史偏好 mood` | 从**行为推断**出来的偏好，比"声明"弱一档。偏好 mood 的算法见下 |
| **同城** | **1** | `content.city == user.city` | 弱相关：同城的人不一定喜欢同一类内容，只是"可能有线下价值" |
| **热度** | **0.5** | `该内容近 7 天 like 数 / 全站最高 like 数`（归一化到 0~1） | 权重必须最低：**热度对所有用户都一样**，权重一高就退化成"全站热榜"，个性化被稀释 |

**排序依据是"信号对个人的针对性"，不是"信号的重要性"。** 一条标准解释四个数字，比四个独立理由更容易自洽。

### 用户情绪偏好怎么算

```sql
SELECT content.mood, SUM(IF(event='like', 3, 1)) AS w
FROM user_event JOIN content ON content.id = user_event.target_id
WHERE user_id = ? AND target_type = 'content' AND content.mood IS NOT NULL
GROUP BY content.mood
ORDER BY w DESC
LIMIT 1
```

把用户的行为和内容表连起来，按情绪分组求加权总分：**点赞记 3、浏览记 1**（浏览可能是误触/扫一眼，点赞是主动表态），取总分最高的情绪。

### 时间衰减为什么用乘法

```
加法：12.5 分的老爆款 − 2 分 = 10.5 分  → 依然霸榜（线性微调）
乘法：12.5 × 0.5^(30/7) ≈ 0.6 分        → 直接沉底（指数打折）
```

"过期就该凉"需要一个**能把它压到底**的机制，加法做不到。半衰期取 7 天，意味着每 7 天分数砍半：`0 天 → 1.0`、`7 天 → 0.5`、`14 天 → 0.25`、`21 天 → 0.125`。

> 这个参数直接决定"新鲜度"与"匹配度"谁更重。改成 30 天半衰期，30 天前的完美匹配就能反超今天的热门。所以它应该用点击率数据来调，而不是拍脑袋。

### 冷启动

判定条件：**没有兴趣标签 且 没有任何行为**。

- 只有一个信号缺失时仍可个性化：有标签就用标签算，有行为就能推出情绪偏好
- 两个都没有 → 四项里三项为 0，算出来的分是假的 → **直接返回近 7 天热门 Top 20**

返回里的 `reason` 字段会写清每一分的来源，例如：

```
标签×3(日常,橘猫,治愈向) + 情绪×2.0 + 同城×1.0 + 热度×0.50 衰减×1.00
```

### 已知局限

1. **全量取内容再在 Python 里打分** —— 24 条没问题，上万条要改成"SQL 粗筛（标签/时间）→ Python 精排"
2. **热度只用 like，没用 view** —— 浏览量大但没人点赞的内容会被低估
3. **不排除已读** —— 用户会看到刚看过的内容
4. **权重是人工设定的** —— 没有数据支撑；严谨做法是用点击率做网格搜索，或引入排序学习
5. **没有评估指标** —— 目前只做了定性验证（两个兴趣不同的用户 top5 完全不同），缺少 NDCG / 点击率这类定量指标

## 测试

```bash
uv run pytest -q
```

前置条件：MySQL 开着、`.env` 存在。
`tests/test_content.py` 用自建夹具（插 3 条 → 测 → 删），不依赖种子数据，覆盖：分页边界、列表不带 body、倒序、详情、404 业务码、参数校验。
`tests/test_event.py` 覆盖：写入回读、`total` 与翻页一致（防 list/count 口径分叉）、非法枚举拒绝。

> 测试是否真的有效，用"故意改坏"来验证：把分页 `offset` 改成固定 0，`test_list_total_matches_across_pages` 应立刻变红。

## 待办

- [x] `content` / `user_event` / `app_user` 三张表
- [x] 埋点接口（浏览 / 点赞）
- [x] 规则版推荐 `GET /feed`（含冷启动兜底与可解释 reason）
- [ ] `cat` 表 + 领养申请：`UPDATE ... WHERE id=? AND status='待领养'` + 判断 rowcount（并发 10 个只成功 1 个）
- [ ] 前端 `/feed` 推荐页（展示"两个兴趣不同的用户看到不同内容"）
- [ ] 前端接埋点（打开详情页自动上报 view）
- [ ] 推荐的自动化测试（top1 差异 / 标签带空格仍匹配 / 冷启动标记）


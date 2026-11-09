# =============================================================================
# app.py —— 应用总入口
# =============================================================================
# 【启动顺序，别打乱】
#   ① 配日志（必须在建 app 之前，否则 FastAPI 自身启动日志抓不到）
#   ② 建 app（FastAPI 实例 + lifespan）
#   ③ 挂中间件：traceid 日志 → CORS（后挂的在外层）
#   ④ 注册全局异常处理器（少了这行，异常会走默认纯文本 500）
#   ⑤ 挂业务路由（按需 include_router）
#
# 【一个请求进来后的链路】
#   客户端 → CORS → traceid 中间件 → 路由函数 → service → repository → MySQL
#           每个环节都能用 async_trace_add_log_record() 记日志（自动带同一个 traceid）
# =============================================================================
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# ① 配日志：必须在创建 app 之前
from exts.logururoute.loguru_config import setup_ext_loguru
setup_ext_loguru()

from db.database import async_engine                        # noqa: E402
from exts.exceptions.exception import ApiExceptionHandler   # noqa: E402
from exts.responses.json_response import Success            # noqa: E402
from middlewares.loger.logmiddleware import setup_log_middleware  # noqa: E402


# ---- lifespan：服务开机 / 关机各跑一次 ---------------------------------------
# yield 之前 = 启动（这里做数据库连通性检查，连不上就别装作活着）
# yield 之后 = 关闭（释放连接池）
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await async_engine.dispose()


# ② 建 app
app = FastAPI(title="Stray Cat Platform", version="0.1.0", lifespan=lifespan)

# ③ 中间件
setup_log_middleware(app)

# CORS 要放在 traceid 中间件之后挂 —— 后挂的在外层，
# 这样即便路由抛错，响应也带跨域头（否则前端只能看到 CORS 错误，看不到真正错误）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ④ 全局异常处理器（漏了这行，业务异常会变成纯文本 500）
ApiExceptionHandler(app)

# ⑤ 业务路由：以后每加一个模块就打开一行
from apis.content.api.content import router_content
app.include_router(router_content)


@app.get("/health", summary="健康检查")
async def health():
    """最简单的一个接口：验证服务活着、中间件生效、统一响应格式正常。"""
    return Success(api_code=200, message="ok", result={"status": "healthy"})

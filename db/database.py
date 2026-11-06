# =============================================================================
# db/database.py —— 数据库连接层（★ 昨天修过的版本，别再用教材原版覆盖）
# =============================================================================
# 【这个文件产出什么】
#   async_engine           : 异步引擎（连接池在它里面）
#   Base                   : 所有 ORM 模型的父类
#   AsyncSessionLocal      : 会话工厂
#   depends_get_db_session : ★ 路由函数用这个（自动 commit / rollback / close）
#   create_all_tables      : 建表
#
# 【★ 相比教材原版，这里修了 5 处（教材那版会踩坑）】
#   1) sessionmaker → async_sessionmaker
#      教材用同步的 sessionmaker 去 bind 异步引擎，运行时才报错
#   2) db_session = AsyncSessionLocal() 提到 try 外面
#      原版写在 try 里，创建失败时 finally 引用它会 UnboundLocalError
#   3) except SQLAlchemyError → except Exception
#      业务代码里的普通异常（raise BusinessError）也要回滚，否则事务悬挂
#   4) raise e → raise
#      raise e 会丢掉原始 traceback，看不到真正出错的行
#   5) 加了 SQLite 分流
#      SQLite 只要文件路径，不能带 host/user/password，否则报 Invalid SQLite URL
# =============================================================================
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config.config import get_settings

Settings = get_settings()

# ---- 1) 构建连接 URL（按数据库类型分流）------------------------------------
if Settings.ASYNC_DB_DRIVER.startswith("sqlite"):
    # SQLite：只要文件路径，不能带 host/user/password
    db_url = f"{Settings.ASYNC_DB_DRIVER}:///{Settings.ASYNC_DB_DATABASE}"
    pool_kwargs = {}
else:
    # MySQL / PostgreSQL：URL.create 比手拼字符串安全（密码含 @ : / 也不会解析错）
    db_url = URL.create(
        drivername=Settings.ASYNC_DB_DRIVER,
        username=Settings.ASYNC_DB_USER,
        password=Settings.ASYNC_DB_PASSWORD,
        host=Settings.ASYNC_DB_HOST,
        port=Settings.ASYNC_DB_PORT,
        database=Settings.ASYNC_DB_DATABASE,
    )
    pool_kwargs = dict(
        pool_size=Settings.ASYNC_DB_POOL_SIZE,
        max_overflow=Settings.ASYNC_DB_MAX_OVERFLOW,
    )

# ---- 2) 创建异步引擎 -------------------------------------------------------
async_engine = create_async_engine(
    db_url,
    echo=Settings.ASYNC_DB_ECHO,
    pool_pre_ping=True,      # 取连接前先 ping，防止拿到 MySQL 已断开的死连接
    **pool_kwargs,
)

# ---- 3) 模型基类 -----------------------------------------------------------
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# ---- 4) 会话工厂 -----------------------------------------------------------
# ★ 必须是 async_sessionmaker，不是 sessionmaker（后者是同步的，配异步引擎会炸）
# ★ expire_on_commit=False 必须：否则 commit 后再访问对象属性会触发隐式查询，
#   异步上下文里报 MissingGreenlet
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# ---- 5) 依赖注入：每个请求一个会话 -----------------------------------------
async def depends_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """路由函数里这样用：

        async def list_doctors(db: AsyncSession = Depends(depends_get_db_session)):
            ...

    不用手动 commit：成功自动提交、异常自动回滚、最后一定 close。
    """
    db_session = AsyncSessionLocal()      # ★ 必须在 try 外面创建
    try:
        yield db_session
        await db_session.commit()         # 正常结束：提交
    except Exception:                     # ★ 用 Exception，不只 SQLAlchemyError
        await db_session.rollback()       # 任何异常：回滚
        raise                             # ★ 裸 raise，保留原始 traceback
    finally:
        await db_session.close()          # 无论如何都关掉，防止连接泄漏


# 别名：项目里有的地方写 get_db_session，有的写 depends_get_db_session，
# 两个名字指向同一个函数，避免到处改名。
get_db_session = depends_get_db_session


# ---- 6) 建表（启动时调一次）------------------------------------------------
async def create_all_tables() -> None:
    """在 app.py 的 lifespan 里调用。

    ★ 必须先 import 所有模型（db/model/__init__.py 里做了），
      否则 Base.metadata 里没有它们，一张表都不会建。
    ★ create_all 只创建不存在的表，不会修改已有表结构。
    """
    import db.model  # noqa: F401  ← 触发模型注册到 Base.metadata
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
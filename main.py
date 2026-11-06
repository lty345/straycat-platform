# =============================================================================
# main.py —— 建表脚本（首次运行 / 加表后各跑一次）
# =============================================================================
# 用法：uv run python main.py
#
# ★ 它只做一件事：把 db/model/ 下注册过的表结构"建出来"。
#   create_all 只创建不存在的表，不会修改已有表的结构。
#   所以：
#     - 加新表        → 跑一次这个脚本
#     - 改已有表的字段 → 这个脚本不管用，得手动 ALTER TABLE（或引入 alembic）
#
# ★ 新增模型后，必须在 db/model/__init__.py 里 import 一次，
#   否则 Base.metadata 里没有它，一张表都不会建。
# =============================================================================
import asyncio

import db.model  # noqa: F401  ← 触发所有模型注册到 Base.metadata
from db.database import async_engine, Base


async def create_tables() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
    print("建表完成")

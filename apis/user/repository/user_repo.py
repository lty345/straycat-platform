from sqlalchemy import func, select

from db.model import AppUser


async def list_users(db, offset: int = 0, limit: int = 50) -> list[AppUser]:
    """分页查用户。

    ★ 显式 order_by：没有排序时 MySQL 不保证顺序，翻页会重复/漏条。
      按 id 升序（先注册的在前）。
    """
    stmt = select(AppUser).order_by(AppUser.id.asc()).offset(offset).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def count_users(db) -> int:
    return (await db.execute(select(func.count()).select_from(AppUser))).scalar_one()

from sqlalchemy import func, select

from db.model import AppUser, Content, UserEvent


async def get_user(db, user_id: int) -> AppUser | None:
    return (await db.execute(select(AppUser).where(AppUser.id == user_id))).scalar_one_or_none()


async def list_all_contents(db) -> list[Content]:
    """取全部内容。

    ★ 为什么是全取：现在只有 24 条，Python 里打分最简单也最好解释。
      内容过万之后要改成"先粗筛（SQL 按标签/时间过滤）再精排"，
      这是 docs/表结构设计.md 里说的"什么时候必须改"。
    """
    return list((await db.execute(select(Content))).scalars().all())


async def like_counts_since(db, since) -> dict[int, int]:
    """近 N 天每条内容的 like 数：{content_id: count}。热度归一化要用它。"""
    stmt = (
        select(UserEvent.target_id, func.count())
        .where(
            UserEvent.target_type == "content",
            UserEvent.event == "like",
            UserEvent.create_time >= since,
        )
        .group_by(UserEvent.target_id)
    )
    rows = (await db.execute(stmt)).all()
    return {target_id: n for target_id, n in rows}


async def preferred_mood(db, user_id: int) -> str | None:
    """用户历史上"看得最多"的 mood（view 权重 1、like 权重 3 —— 点赞更能说明偏好）。

    返回 None 表示算不出来（新用户、没有任何行为、或行为指向的内容都删了）。
    """
    weight = func.sum(func.if_(UserEvent.event == "like", 3, 1))
    stmt = (
        select(Content.mood, weight.label("w"))
        .join(Content, Content.id == UserEvent.target_id)
        .where(
            UserEvent.user_id == user_id,
            UserEvent.target_type == "content",
            Content.mood.is_not(None),
        )
        .group_by(Content.mood)
        .order_by(weight.desc())
        .limit(1)
    )
    row = (await db.execute(stmt)).first()
    return row[0] if row else None


async def has_events(db, user_id: int) -> bool:
    stmt = select(func.count()).select_from(UserEvent).where(UserEvent.user_id == user_id)
    return (await db.execute(stmt)).scalar_one() > 0

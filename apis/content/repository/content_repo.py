
from sqlalchemy import select, func
from sqlalchemy import or_

from db.model import Content


async def get_content_by_id(db, content_id) -> Content | None:
    return (await db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()

def _apply_filters(stmt, mood: str | None, keyword: str | None):
    if mood:
        stmt = stmt.where(Content.mood == mood)                       # 空 1：mood 精确匹配
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(
            Content.title.like(like), Content.summary.like(like), Content.tags.like(like)                          # 空 2：title / summary / tags 三列
        ))
    return stmt

async def list_contents(db, offset=0, limit=100, mood=None, keyword=None):
    stmt=select(Content)
    stmt=_apply_filters(stmt,mood,keyword)
    stmt = stmt.order_by(Content.pub_time.desc(), Content.id.desc()).offset(offset).limit(limit)
    return (await db.execute(stmt)).scalars().all()

async def count_contents(db, mood=None, keyword=None):
    stmt=select(func.count()).select_from(Content)
    stmt=_apply_filters(stmt,mood,keyword)
    return (await db.execute(stmt)).scalar_one()
from sqlalchemy import select, func

from db.model import Content

async def list_contents(db, offset: int = 0, limit: int = 100) -> list[Content]:
    return (await db.execute(select(Content).offset(offset).limit(limit))).scalars().all()

async def count_contents(db) -> int:
    return (await db.execute(select(func.count()).select_from(Content))).scalar_one()

from sqlalchemy import select, func


from db.model import UserEvent


async def create_event(db, *, user_id, target_type, target_id, event, duration_ms=None) -> UserEvent:
    """插一条埋点。★ 不 commit —— 由 get_db_session 在请求成功时统一提交。"""
    row = UserEvent(
        user_id=user_id,          # 空 1：模型里对应"谁"的字段名
        target_type=target_type,      # 空 2：对应"行为对象类型"的字段名
        target_id=target_id,
        event=event,
        duration_ms=duration_ms,
    )
    db.add(row)
    await db.flush()           # ★ flush 才会把 INSERT 发给数据库、并把自增 id 填回 row.id
    return row

async def get_events(db, user_id, target_type, event, page, page_size) -> list[UserEvent]:
    """根据条件查询埋点。"""
    query = select(UserEvent).where(
        UserEvent.user_id == user_id,
    ).offset((page - 1) * page_size).limit(page_size).order_by(UserEvent.create_time.desc(), UserEvent.id.desc())
    query = _apply_filters(query, target_type, event)
    result = await db.execute(query)
    return result.scalars().all()

def _apply_filters(stmt, target_type, event):
    if target_type:
        stmt = stmt.where(UserEvent.target_type == target_type)
    if event:
        stmt = stmt.where(UserEvent.event == event)
    return stmt

async def count_events(db, user_id, target_type, event):
    stmt = select(func.count()).select_from(UserEvent).where(UserEvent.user_id == user_id)
    stmt = _apply_filters(stmt, target_type, event)
    return (await db.execute(stmt)).scalar_one()

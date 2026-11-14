from fastapi import APIRouter, Depends
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession
from exts.schemas.page import Page
from apis.event.repository import event_repo
from apis.event.schemas.event import EventIn, EventOut
from db.database import get_db_session
from exts.responses.json_response import Success

router_event = APIRouter(prefix="/api/v1", tags=["埋点"])


@router_event.post("/events", summary="记录一次行为")
async def create_event(payload: EventIn, db: AsyncSession = Depends(get_db_session)):
    """写一条埋点（浏览 / 点赞）。公开接口，埋点丢了不致命，所以不做复杂校验。"""
    row = await event_repo.create_event(db, **payload.model_dump())
    return Success(api_code=200, message="记录成功", result={"id": row.id})

@router_event.get("/users/{user_id}/events", summary="查询埋点数据")
async def get_events(user_id: int,
                     target_type: str | None = Query(None, description="content / cat"),
                     event: str | None = Query(None, description="view / like"),
                     page: int=Query(1, ge=1),
                     page_size: int=Query(10, ge=1, le=20),
                     db: AsyncSession = Depends(get_db_session)):
    """根据条件查询埋点。"""
    rows = await event_repo.get_events(db, user_id=user_id, target_type=target_type, event=event, page=page, page_size=page_size)
    total = await event_repo.count_events(db, user_id=user_id, target_type=target_type, event=event)
    return Success(api_code=200, message="查询成功", result=Page[EventOut](total=total, list=[EventOut.model_validate(r) for r in rows], page=page, page_size=page_size))

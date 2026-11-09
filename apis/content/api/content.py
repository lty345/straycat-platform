from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apis.content.repository import content_repo
from apis.content.schemas.content import ContentOut
from db.database import get_db_session
from exts.responses.json_response import Success
from exts.schemas.page import Page

router_content = APIRouter(prefix="/api/v1", tags=["内容"])


@router_content.get("/contents", summary="内容列表")
async def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """分页查内容。公开接口，不需要登录。"""
    # TODO(你)：
    #   1. offset = (page - 1) * page_size
    #   2. rows  = await content_repo.list_contents(db, offset=offset, limit=page_size)
    #   3. total = await content_repo.count_contents(db)
    #   4. data  = [ContentOut.model_validate(r) for r in rows]
    #   5. return Success(api_code=200, message="获取成功", result=Page[ContentOut](...))
    offset = (page - 1) * page_size
    rows = await content_repo.list_contents(db, offset=offset, limit=page_size)
    total = await content_repo.count_contents(db)
    data = [ContentOut.model_validate(r) for r in rows]
    return Success(api_code=200, message="获取成功", result=Page[ContentOut](total=total, list=data, page=page, page_size=page_size))

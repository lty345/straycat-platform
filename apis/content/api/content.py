from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from apis.content.repository import content_repo
from apis.content.schemas.content import ContentListOut, ContentDetailOut
from db.database import get_db_session
from exts.exceptions.exception import BusinessError, ExceptionEnum
from exts.responses.json_response import Success
from exts.schemas.page import Page

router_content = APIRouter(prefix="/api/v1", tags=["内容"])


@router_content.get("/contents", summary="内容列表")
async def list_contents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    mood: str | None = Query(None, description="情绪基调：治愈/科普/揪心/欢乐"),
    keyword: str | None = Query(None, max_length=50, description="关键词，匹配标题/摘要/标签"),
    db: AsyncSession = Depends(get_db_session),
):
    """分页查内容。公开接口，不需要登录。"""

    offset = (page - 1) * page_size
    rows = await content_repo.list_contents(db, offset=offset, limit=page_size, mood=mood, keyword=keyword)
    total = await content_repo.count_contents(db, mood=mood, keyword=keyword)
    data = [ContentListOut.model_validate(r) for r in rows]
    return Success(api_code=200, message="获取成功", result=Page[ContentListOut](total=total, list=data, page=page, page_size=page_size))

@router_content.get("/contents/{content_id}", summary="内容详情")
async def get_content_detail(
        content_id: int = Path(...,ge=1, description="内容 id"),
        db: AsyncSession = Depends(get_db_session)):
    """查内容详情。公开接口，不需要登录。"""
    row = await content_repo.get_content_by_id(db, content_id)
    if row is None:
        raise BusinessError(ExceptionEnum.CONTENT_NOT_FOUND)
    data = ContentDetailOut.model_validate(row)
    return Success(api_code=200, message="获取成功", result=data)

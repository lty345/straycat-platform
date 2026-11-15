from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apis.cat.repository import cat_repo
from apis.cat.schemas.cat import AdoptIn, CatOut
from db.database import get_db_session
from exts.exceptions.exception import BusinessError, ExceptionEnum
from exts.responses.json_response import Success
from exts.schemas.page import Page

router_cat = APIRouter(prefix="/api/v1", tags=["领养"])


@router_cat.get("/cats", summary="猫列表")
async def list_cats(
    status: str | None = Query(None, description="待领养 / 审核中 / 已领养"),
    city: str | None = Query(None, description="城市，如 广州"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """分页查猫。两个筛选都是可选的。

    ★ 为什么 status/city 是可选的：前端有三种用法——
      领养页只要「待领养」、后台要「全部」、按城市筛则再叠加 city。
      全都做成可选，一个接口够用。
    """
    offset = (page - 1) * page_size
    rows = await cat_repo.list_cats(
        db, offset=offset, limit=page_size, status=status, city=city
    )
    total = await cat_repo.count_cats(db, status=status, city=city)

    data = [CatOut.model_validate(r) for r in rows]
    return Success(
        api_code=200,
        message="获取成功",
        result=Page[CatOut](
            total=total, list=data, page=page, page_size=page_size
        ),
    )


@router_cat.post("/cats/{cat_id}/adopt", summary="申请领养一只猫")
async def adopt_cat(
    cat_id: int = Path(..., ge=1, description="猫的 id"),
    payload: AdoptIn = ...,
    db: AsyncSession = Depends(get_db_session),
):
    """申请领养。抢到返回成功；被别人抢先返回业务码 20001。"""
    ok = await cat_repo.adopt_cat(db, cat_id, payload.user_id)
    if not ok:
        raise BusinessError(ExceptionEnum.ADOPT_TAKEN)
    return Success(api_code=200, message="申请成功", result={"cat_id": cat_id, "status": "审核中"})

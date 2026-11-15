from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from apis.cat.repository import cat_repo
from apis.cat.schemas.cat import AdoptIn
from db.database import get_db_session
from exts.exceptions.exception import BusinessError, ExceptionEnum
from exts.responses.json_response import Success

router_cat = APIRouter(prefix="/api/v1", tags=["领养"])


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
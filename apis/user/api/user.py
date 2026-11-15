from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apis.user.repository import user_repo
from apis.user.schemas.user import UserOut
from db.database import get_db_session
from exts.responses.json_response import Success
from exts.schemas.page import Page

router_user = APIRouter(prefix="/api/v1", tags=["用户"])


@router_user.get("/users", summary="用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """列出用户。

    ★ 这个接口是给"演示/开发"用的：前端的"切换用户看推荐"需要知道有哪些用户，
      而不是把 id=4/5/6 写死在前端 —— 一旦重新造种子数据，写死的 id 就全错了。
      真实系统里用户列表属于后台功能，需要权限。
    """
    offset = (page - 1) * page_size
    rows = await user_repo.list_users(db, offset=offset, limit=page_size)
    total = await user_repo.count_users(db)

    return Success(
        api_code=200,
        message="获取成功",
        result=Page[UserOut](
            total=total,
            list=[UserOut.model_validate(r) for r in rows],
            page=page,
            page_size=page_size,
        ),
    )

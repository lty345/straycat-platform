"""鉴权依赖：从请求头里解出"当前登录用户"。

FastAPI 的依赖注入让接口只要写 `user=Depends(get_current_user)`，
就能拿到已登录用户，不用每个接口自己解析 token。
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from apis.auth.repository import auth_repo
from db.database import get_db_session
from exts.exceptions.exception import BusinessError, ExceptionEnum
from exts.security import decode_access_token

# auto_error=False：没带 token 时不让 FastAPI 直接甩 403，
# 而是交给我们的异常处理器，返回统一格式
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db_session),
):
    """从 Authorization: Bearer <token> 解出当前用户。

    三步校验：
      ① token 存在且格式对
      ② 签名/过期时间都对（decode 内部验签）
      ③ 用户还在，且是可登录用户（username 不为空）

    ★ 第 ③ 步必须查库：token 只证明"7 天前登录过"，
      中间账号可能被删、被禁用、改了密码 —— 只有查库才能发现。
      代价是一次主键查询，走索引，微秒级。
    """
    if creds is None:
        raise BusinessError(ExceptionEnum.TOKEN_INVALID)

    user_id = decode_access_token(creds.credentials)
    if user_id is None:
        raise BusinessError(ExceptionEnum.TOKEN_INVALID)

    user = await auth_repo.get_by_id(db, user_id)
    if user is None or not user.username:
        raise BusinessError(ExceptionEnum.TOKEN_INVALID)
    return user

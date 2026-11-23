from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apis.auth.deps import get_current_user
from apis.auth.repository import auth_repo
from apis.auth.schemas.auth import AuthUserOut, LoginIn, RegisterIn, TokenOut
from db.database import get_db_session
from exts.exceptions.exception import BusinessError, ExceptionEnum
from exts.responses.json_response import Success
from exts.security import (
    MAX_PASSWORD_BYTES,
    TOKEN_EXPIRE_DAYS,
    create_access_token,
    hash_password,
    verify_password,
)

router_auth = APIRouter(prefix="/api/v1/auth", tags=["认证"])


def _token_out(user) -> TokenOut:
    return TokenOut(
        token=create_access_token(user.id),
        expires_in=TOKEN_EXPIRE_DAYS * 86400,
        user=AuthUserOut.model_validate(user),
    )


@router_auth.post("/register", summary="注册")
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db_session)):
    """注册成功直接返回 token（注册即登录）。"""
    # bcrypt 只认前 72 字节，超了会被静默截断 —— 必须显式拒绝
    if len(payload.password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise BusinessError(ExceptionEnum.PARAMETER_ERROR, err_code_des="密码过长（最多 72 字节）")

    if await auth_repo.get_by_username(db, payload.username):
        raise BusinessError(ExceptionEnum.USERNAME_TAKEN)      # 常见情况：给友好提示

    try:
        user = await auth_repo.create_user(
            db,
            username=payload.username,
            password_hash=hash_password(payload.password),
            nickname=payload.nickname,
            city=payload.city,
            interest_tags=payload.interest_tags,
        )
    except IntegrityError:
        # 并发兜底：两个请求同时注册同名，数据库唯一索引会拦住一个
        raise BusinessError(ExceptionEnum.USERNAME_TAKEN)

    return Success(result=_token_out(user), message="注册成功")


@router_auth.post("/login", summary="登录")
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db_session)):
    """用户名 + 密码 → token。

    ★ 失败一律提示"用户名或密码错误"，不区分"没这人"和"密码错"，
      否则攻击者可以批量探测哪些用户名已注册（用户枚举）。
    """
    user = await auth_repo.get_by_username(db, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise BusinessError(ExceptionEnum.LOGIN_FAILED)
    return Success(result=_token_out(user), message="登录成功")


@router_auth.get("/me", summary="当前登录用户")
async def me(user=Depends(get_current_user)):
    """前端刷新页面后，用本地 token 换回用户信息。

    没带 token / token 过期 → 10401，前端据此清 token 并跳登录。
    """
    return Success(result=AuthUserOut.model_validate(user))

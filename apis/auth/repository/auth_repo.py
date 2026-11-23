from sqlalchemy import select

from db.model import AppUser


async def get_by_username(db, username: str) -> AppUser | None:
    """按登录名查用户（登录 / 注册查重用）。"""
    stmt = select(AppUser).where(AppUser.username == username)
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_user(
    db,
    *,
    username: str,
    password_hash: str,
    nickname: str | None = None,
    city: str | None = None,
    interest_tags: str | None = None,
) -> AppUser:
    """建用户。

    ★ 只 flush 不 commit：把 id 取回来，事务交给 get_db_session 在响应后统一提交。
      这样"注册"和后续操作能在一个事务里。
    ★ flush 会立刻发 INSERT，所以用户名撞车（唯一索引）会在这里抛 IntegrityError，
      api 层能就地捕获转成友好提示。
    """
    user = AppUser(
        username=username,
        password_hash=password_hash,
        nickname=nickname or username,   # 没填昵称就用用户名
        city=city,
        interest_tags=interest_tags,
    )
    db.add(user)
    await db.flush()
    return user


async def get_by_id(db, user_id: int) -> AppUser | None:
    """按主键查用户（鉴权依赖每次请求都要用，必须走主键索引）。"""
    return await db.get(AppUser, user_id)

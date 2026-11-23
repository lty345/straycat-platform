"""密码哈希与 JWT：登录的密码学部分都收在这里。

为什么要单独一层：
    api 层只关心"注册/登录流程"，不关心 bcrypt 参数、JWT 算法这些细节。
    以后要换算法（比如 argon2）只改这个文件。
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from config.config import get_settings

Settings = get_settings()

ALGORITHM = "HS256"          # HMAC + SHA256：对称签名，单服务部署够用
TOKEN_EXPIRE_DAYS = 7        # 7 天免登录
BCRYPT_ROUNDS = 12           # 越大越慢越安全；12 ≈ 单次 250ms
MAX_PASSWORD_BYTES = 72      # bcrypt 硬限制：超过 72 字节会被静默截断


def hash_password(plain: str) -> str:
    """注册/改密时用：明文 → bcrypt 哈希（自带随机盐）。"""
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode("utf-8")


def verify_password(plain: str, hashed: str | None) -> bool:
    """登录时用：明文 + 哈希 → 是否匹配。

    hashed 为空（演示用户）直接返回 False，不给登录。
    """
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False          # 哈希格式不合法（比如被手改过）


def create_access_token(user_id: int) -> str:
    """登录/注册成功后签发。"""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),                              # JWT 规范：sub = 主体标识
        "iat": now,                                       # 签发时间
        "exp": now + timedelta(days=TOKEN_EXPIRE_DAYS),    # 过期时间
    }
    return jwt.encode(payload, Settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """每次请求验签；失败返回 None（过期 / 伪造 / 格式错都算失败）。"""
    try:
        payload = jwt.decode(token, Settings.SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None

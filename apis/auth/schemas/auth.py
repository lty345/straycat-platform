from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    """注册入参。

    ★ username 限制成字母数字下划线：避免用户名里出现空格/表情/特殊符号，
      以后做 URL、@ 提及、日志检索都不会出问题。
    ★ password 只做长度约束，不强制复杂度（强制复杂度的副作用是用户写在便利贴上）。
    """

    username: str = Field(pattern=r"^[A-Za-z0-9_]{3,32}$")
    password: str = Field(min_length=8, max_length=64)
    nickname: str | None = Field(default=None, max_length=50)
    city: str | None = Field(default=None, max_length=50)
    interest_tags: str | None = Field(default=None, max_length=255)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=64)


class AuthUserOut(BaseModel):
    """返回给前端的用户信息。

    ★ 这里没有 password_hash —— 响应模型是"最后一道防泄漏"，只要不在模型里定义，
      就算有人往里面塞了也会被过滤掉。
    """

    id: int
    username: str | None = None
    nickname: str | None = None
    city: str | None = None
    interest_tags: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    """注册/登录成功的返回。

    expires_in 给前端一个"什么时候该重新登录"的依据。
    """

    token: str
    expires_in: int
    user: AuthUserOut

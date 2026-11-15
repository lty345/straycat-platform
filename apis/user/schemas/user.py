from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    """用户基本信息。

    ★ 为什么不返回 create_time 之类的内部字段：
      前端"选一个用户看看推荐"只需要 id / 昵称 / 兴趣标签，
      多给的字段将来都是兼容负担。
    """

    id: int
    nickname: str | None = None
    city: str | None = None
    interest_tags: str | None = None

    model_config = ConfigDict(from_attributes=True)

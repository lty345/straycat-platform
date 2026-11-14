from datetime import datetime

from pydantic import BaseModel


class FeedItem(BaseModel):
    """推荐流里的一条：内容基本信息 + 分数 + 理由。

    ★ 为什么要返回 score 和 reason：
      这是"可解释推荐"的落点。前端能显示"因为你也喜欢橘猫"，
      面试时你也有一份能指着讲的东西。
    """

    id: int
    title: str
    summary: str | None = None
    tags: str | None = None
    mood: str | None = None
    city: str | None = None
    cover_url: str | None = None
    pub_time: datetime | None = None

    score: float
    reason: str


class FeedPage(BaseModel):
    """推荐流返回。total 是"参与排序的内容总数"，不是库里内容总数。"""

    list: list[FeedItem]
    total: int
    cold_start: bool          # true 表示走的是热门兜底，不是个性化排序
    preferred_mood: str | None = None   # 顺便告诉前端"系统认为你偏好什么情绪"

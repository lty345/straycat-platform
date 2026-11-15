from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdoptIn(BaseModel):
    user_id: int


class CatOut(BaseModel):
    """领养列表里的一只猫。

    ★ 和 ContentListOut 的三个共同点：
      ① from_attributes=True —— 允许直接从 ORM 对象转
      ② 不含"内部字段"（这里没有，但将来若有内部备注就别暴露）
      ③ 状态/城市这类枚举值原样返回字符串，前端自己决定怎么显示
    """

    id: int
    name: str
    breed: str | None = None
    age_month: int | None = None
    health: str | None = None
    city: str | None = None
    status: str                      # 待领养 / 审核中 / 已领养
    applicant_id: int | None = None  # 前端可以据此显示"你已申请"
    cover_url: str | None = None
    create_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

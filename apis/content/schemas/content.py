from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ContentOut(BaseModel):
    id: int
    title: str
    summary: str | None = None
    body: str | None = None
    tags: str | None = None
    mood: str | None = None
    cover_url: str | None = None
    pub_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)   # 允许从 ORM 对象直接转换

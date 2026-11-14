import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class EventIn(BaseModel):
    """埋点入参。target_type 和 event 用 Literal 锁死取值，写错自动 400。"""
    user_id: int
    target_type: Literal["content", "cat"]
    target_id: int
    event: Literal["view", "like"]
    duration_ms: int | None = None   # view 时可带停留时长，like 不传

class EventOut(BaseModel):
    """埋点出参。"""
    id: int
    user_id: int
    target_type: Literal["content", "cat"]
    target_id: int
    event: Literal["view", "like"]
    duration_ms: int | None = None
    create_time: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

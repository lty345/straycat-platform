from pydantic import BaseModel


class AdoptIn(BaseModel):
    user_id: int
from datetime import datetime
from pydantic import BaseModel, ConfigDict




class ContentListOut(BaseModel):
    #id / title / summary / tags / mood / cover_url / pub_time
    id:int
    title:str
    summary:str | None = None
    tags:str | None = None
    mood:str | None = None
    cover_url:str | None = None
    pub_time:datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class ContentDetailOut(ContentListOut):
    body:str | None = None

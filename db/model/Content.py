from db.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime,Index
from sqlalchemy import func

class Content(Base):
    __tablename__ = 'content'
    __table_args__ = (
        Index("idx_pub_time", "pub_time"),   # 时间衰减要用
        Index("idx_mood", "mood"),           # 按情绪筛选要用
        {"comment": "内容表"},
    )
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(500))
    body = Column(Text)
    tags = Column(String(255))
    mood=Column(String(16),comment="治愈/科普/揪心/欢乐/其他")
    city=Column(String(50),comment="内容所在城市，推荐的同城加权用")
    cover_url=Column(String(500))
    pub_time=Column(DateTime,server_default=func.now())
    create_time=Column(DateTime,server_default=func.now())

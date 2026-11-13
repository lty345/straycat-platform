from db.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Index, BigInteger
from sqlalchemy import func

class UserEvent(Base):
    __tablename__ = "user_event"
    __table_args__ = (
        Index("idx_user_time", "user_id", "create_time"),
        Index("idx_target", "target_type", "target_id"),
        {"comment": "用户行为埋点"})
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    target_type = Column(String(16), nullable=False)
    target_id = Column(Integer, nullable=False)
    event = Column(String(16), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    create_time = Column(DateTime, server_default=func.now())

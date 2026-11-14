from sqlalchemy import Column, Integer, String, DateTime, func
from db.database import Base


class AppUser(Base):
    __tablename__ = "app_user"
    __table_args__ = ({"comment": "用户表"},)

    id = Column(Integer, primary_key=True)
    nickname = Column(String(50))
    city = Column(String(50))
    interest_tags = Column(String(255))
    create_time = Column(DateTime, server_default=func.now(), nullable=False)

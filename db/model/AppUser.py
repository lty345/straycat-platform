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

    # ---- 登录相关 ----
    # username：登录名，唯一。演示用户留空 → 不能登录，但推荐数据仍可用
    username = Column(String(50), unique=True, index=True, nullable=True)
    # password_hash：bcrypt 哈希（60 字符左右，留 255 余量）
    password_hash = Column(String(255), nullable=True)

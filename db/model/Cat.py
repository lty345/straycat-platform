from sqlalchemy import Column, Integer, String, DateTime, Index, func

from db.database import Base


class Cat(Base):
    __tablename__ = "cat"
    __table_args__ = (
        Index("idx_status_city", "status", "city"),                    # 空1：索引 idx_status_city，建在 (status, city) 两列上
        Index("idx_applicant", "applicant_id"),                    # 空2：索引 idx_applicant，建在 applicant_id 上
        {"comment": "待领养的猫"},
    )

    id = Column(Integer, primary_key=True)          # ★ 不写 index=True
    name = Column(String(50), nullable=False)
    breed = Column(String(30))
    age_month = Column(Integer)
    health = Column(String(50))
    city = Column(String(50))
    status = Column(String(16), nullable=False, server_default="待领养")   # 空3：默认值 '待领养'
    applicant_id = Column(Integer)
    content_id = Column(Integer)
    cover_url = Column(String(500))
    create_time = Column(DateTime, server_default=func.now(), nullable=False)
from sqlalchemy import Column, Integer, BigInteger, DateTime, func
from database import Base

class ApprovedUser(Base):
    __tablename__ = "approved_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    approved_at = Column(DateTime(timezone=True), server_default=func.now())

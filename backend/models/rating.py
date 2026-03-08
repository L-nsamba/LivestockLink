from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.mysql import CHAR

#Skeleton for rating table
class Rating(Base):
    __tablename__="rating"

    rating_id = Column(CHAR(36), primary_key=True, nullable=False)
    farmer_id = Column(CHAR(36), nullable=False)
    transporter_id = Column(CHAR(36), nullable=False)
    rating_value = Column(Integer, nullable=False)
    comment = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

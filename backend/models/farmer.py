from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import CHAR

# Skeleton for farmers table
class Farmer(Base):
    __tablename__ = "farmer"
    user_id = Column(CHAR(36), primary_key=True, nullable=False)
    farm_location = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
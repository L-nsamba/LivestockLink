from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime

# Skeleton for farmers table
class Farmer(Base):
    __tablename__ = "farmer"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    farm_location = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
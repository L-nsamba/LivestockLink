from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Integer, Column, String, Enum, DateTime

# Creation of skeleton for transporter
class Transporter(Base):
    __tablename__ = "transporter"
    user_id = Column(Integer, primary_key=True, nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    vehicle_capacity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
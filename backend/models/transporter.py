from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Integer, Column, String, DateTime
from sqlalchemy.dialects.mysql import CHAR

# Creation of skeleton for transporter
class Transporter(Base):
    __tablename__ = "transporter"
    user_id = Column(CHAR(36), primary_key=True, nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    vehicle_capacity = Column(Integer, nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    organization_name = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
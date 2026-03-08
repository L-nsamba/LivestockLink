import uuid
from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey


class TransportRequest(Base):
    __tablename__ = "transport_requests"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    pickup_location = Column(String(150), nullable=False)
    destination_location = Column(String(150), nullable=False)
    pickup_date = Column(DateTime, nullable=False)
    animal_type = Column(String(50), nullable=False)
    animal_quantity = Column(Integer, nullable=False)
    status = Column(
        Enum('PENDING', 'BOOKED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED'),
        nullable=False,
        default='PENDING'
    )
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

import uuid
from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import CHAR


class Bookings(Base):
    __tablename__ = "bookings"
    booking_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(CHAR(36), ForeignKey("transport_requests.request_id"), nullable=False, unique=True)
    transporter_id = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False)

    accepted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(
        Enum('ACCEPTED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED'),
        nullable=False,
        default='ACCEPTED'
    )

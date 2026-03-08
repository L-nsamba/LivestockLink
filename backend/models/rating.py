import uuid

from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship

#Skeleton for rating table
class Rating(Base):
    __tablename__="ratings"

    rating_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    booking_id = Column(CHAR(36), ForeignKey("bookings.booking_id"), nullable=False)
    rating_by = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False)
    rating_for = Column(CHAR(36), ForeignKey("users.user_id"), nullable=False)

    score = Column(Integer, nullable=False) #1-5
    comment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    booking = relationship("Bookings", back_populates="ratings")
    rater = relationship("User", foreign_keys=[rating_by])
    rated_user = relationship("User", foreign_keys=[rating_for])

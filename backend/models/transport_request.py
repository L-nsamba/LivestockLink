import uuid
from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, DateTime, Text, Float, ForeignKey
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship


class TransportRequest(Base):
    __tablename__ = "transport_request"

    # Primary key
    request_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys linking to farmer and transporter
    farmer_id = Column(CHAR(36), ForeignKey("farmer.user_id"), nullable=False)
    transporter_id = Column(CHAR(36), ForeignKey("transporter.user_id"), nullable=True)  # Nullable until assigned

    # Cargo details
    cargo_description = Column(Text, nullable=False)
    cargo_weight_kg = Column(Float, nullable=False)

    # Location details
    pickup_location = Column(String(200), nullable=False)
    dropoff_location = Column(String(200), nullable=False)

    # Scheduling
    requested_date = Column(DateTime, nullable=False)

    # Request lifecycle status
    status = Column(
        Enum('PENDING', 'ACCEPTED', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED'),
        nullable=False,
        default='PENDING'
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # Relationships for easy access to related objects
    farmer = relationship("Farmer", backref="transport_requests", foreign_keys=[farmer_id])
    transporter = relationship("Transporter", backref="assigned_requests", foreign_keys=[transporter_id])

    def __repr__(self):
        return (
            f"<TransportRequest(request_id={self.request_id}, "
            f"status={self.status}, "
            f"farmer_id={self.farmer_id}, "
            f"transporter_id={self.transporter_id})>"
        )

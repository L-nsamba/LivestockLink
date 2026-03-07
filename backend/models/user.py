import uuid
from database.db import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.dialects.mysql import CHAR

# Definition of the user table with sqlalchemy
class User(Base):
    __tablename__ = 'users'
    user_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100), nullable=False)
    contact = Column(String(25), nullable=False)
    password_hash = Column(String(225), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role = Column(Enum('FARMER', 'TRANSPORTER', 'ADMIN'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

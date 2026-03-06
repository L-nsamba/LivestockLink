from database.db import Base
from sqlalchemy import Column, Integer, String, Enum

# Definition of the user table with sqlalchemy
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    contact = Column(String(25), nullable=False)
    password_hash = Column(String(225), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    role = Column(Enum('FARMER', 'TRANSPORTER', 'ADMIN'), nullable=False)
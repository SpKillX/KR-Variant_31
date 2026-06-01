from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from ..db.session import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CLIENT = "client"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CLIENT, nullable=False)

    bookings = relationship("Booking", back_populates="user")

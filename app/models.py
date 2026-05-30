from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    
    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")

class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    number = Column(Integer, nullable=False)
    capacity = Column(Integer, default=2)
    is_available = Column(Boolean, default=True)
    
    restaurant = relationship("Restaurant", back_populates="tables")
    bookings = relationship("Booking", back_populates="table", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    booking_time = Column(DateTime, default=datetime.datetime.utcnow)
    
    table = relationship("Table", back_populates="bookings")

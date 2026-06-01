from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, Time
from sqlalchemy.orm import relationship
from app.db.session import Base
import datetime

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    opening_time = Column(Time, nullable=False, default="09:00")
    closing_time = Column(Time, nullable=False, default="23:00")
    
    zones = relationship("Zone", back_populates="restaurant", cascade="all, delete-orphan")

class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    name = Column(String, nullable=False) # Например: "Основной зал", "Терраса", "VIP-зона"
    
    restaurant = relationship("Restaurant", back_populates="zones")
    tables = relationship("Table", back_populates="zone", cascade="all, delete-orphan")

class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    number = Column(Integer, nullable=False)
    capacity = Column(Integer, default=2)
    
    # Координаты для визуализации на карте зала
    x_coord = Column(Float, default=0.0)
    y_coord = Column(Float, default=0.0)
    
    zone = relationship("Zone", back_populates="tables")
    bookings = relationship("Booking", back_populates="table", cascade="all, delete-orphan")

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    table = relationship("Table", back_populates="bookings")

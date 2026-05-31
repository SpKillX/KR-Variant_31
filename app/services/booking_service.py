from sqlalchemy.orm import Session
from ..models import booking as models
from ..schemas import booking as schemas
from datetime import datetime

def get_restaurants(db: Session):
    return db.query(models.Restaurant).all()

def get_restaurant(db: Session, restaurant_id: int):
    return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

def get_tables_by_restaurant(db: Session, restaurant_id: int):
    return db.query(models.Table).filter(models.Table.restaurant_id == restaurant_id).all()

def create_booking(db: Session, booking: schemas.BookingCreate):
    # Check if table is available
    table = db.query(models.Table).filter(models.Table.id == booking.table_id).first()
    if not table or not table.is_available:
        return None
    
    db_booking = models.Booking(
        table_id=booking.table_id,
        customer_name=booking.customer_name,
        booking_time=booking.booking_time
    )
    table.is_available = False
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def cancel_booking(db: Session, booking_id: int):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking:
        table = db.query(models.Table).filter(models.Table.id == db_booking.table_id).first()
        if table:
            table.is_available = True
        db.delete(db_booking)
        db.commit()
        return True
    return False

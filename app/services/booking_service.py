from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import booking as models
from ..schemas import booking as schemas
from datetime import datetime

class BookingService:
    @staticmethod
    def is_table_available(db: Session, table_id: int, start_time: datetime, end_time: datetime) -> bool:
        """
        Checks if a table is available for a given time interval.
        Intervals overlap if (StartA < EndB) AND (EndA > StartB).
        """
        overlapping_bookings = db.query(models.Booking).filter(
            and_(
                models.Booking.table_id == table_id,
                models.Booking.start_time < end_time,
                models.Booking.end_time > start_time
            )
        ).first()

        return overlapping_bookings is None

    @staticmethod
    def create_booking(db: Session, booking_data: schemas.BookingCreate):
        # 1. Dynamic Availability Check
        if not BookingService.is_table_available(db, booking_data.table_id, booking_data.start_time, booking_data.end_time):
            return None

        # 2. Create Booking
        db_booking = models.Booking(
            table_id=booking_data.table_id,
            customer_name=booking_data.customer_name,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

    @staticmethod
    def cancel_booking(db: Session, booking_id: int) -> bool:
        db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
        if db_booking:
            db.delete(db_booking)
            db.commit()
            return True
        return False

    @staticmethod
    def get_table_availability(db: Session, table_id: int, date: datetime):
        """Returns all bookings for a table on a specific date to help UI visualize occupied slots."""
        return db.query(models.Booking).filter(
            models.Booking.table_id == table_id,
            models.Booking.start_time >= date.replace(hour=0, minute=0, second=0),
            models.Booking.end_time <= date.replace(hour=23, minute=59, second=59)
        ).all()


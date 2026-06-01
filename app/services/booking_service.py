from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models import booking as models
from app.schemas import booking as schemas
from app.core.config import settings
from datetime import datetime, time
import datetime as dt

class BookingService:
    @staticmethod
    def is_table_available(db: Session, table_id: int, start_time: datetime, end_time: datetime) -> bool:
        """
        Checks if a table is available for a given time interval.
        Intervals overlap if (StartA < EndB) AND (EndA > StartB).
        """
        # Check Restaurant Working Hours
        table = db.query(models.Table).filter(models.Table.id == table_id).first()
        if not table:
            return False
            
        zone = db.query(models.Zone).filter(models.Zone.id == table.zone_id).first()
        restaurant = db.query(models.Restaurant).filter(models.Restaurant.id == zone.restaurant_id).first()
        
        # Convert booking times to time objects for comparison
        booking_start = start_time.time()
        booking_end = end_time.time()
        
        # Fix for midnight closing time: treat 00:00 as 23:59:59
        actual_closing_time = restaurant.closing_time
        if actual_closing_time == time(0, 0):
            actual_closing_time = time(23, 59, 59)

        if booking_start < restaurant.opening_time or booking_end > actual_closing_time:
            return False

        overlapping_bookings = db.query(models.Booking).filter(
            and_(
                models.Booking.table_id == table_id,
                models.Booking.start_time < end_time,
                models.Booking.end_time > start_time
            )
        ).first()

        return overlapping_bookings is None

    @staticmethod
    def create_booking(db: Session, booking_data: schemas.BookingCreate, user_id: int = None):
        # Duration validation
        duration = (booking_data.end_time - booking_data.start_time).total_seconds() / 60
        if duration < settings.MIN_BOOKING_DURATION or duration > settings.MAX_BOOKING_DURATION:
            return "duration_error"

        if not BookingService.is_table_available(db, booking_data.table_id, booking_data.start_time, booking_data.end_time):
            return None

        db_booking = models.Booking(
            table_id=booking_data.table_id,
            user_id=user_id,
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
    def update_booking(db: Session, booking_id: int, update_data: dict):
        db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
        if not db_booking:
            return None
        
        # If table or time is changing, check availability and duration
        if 'table_id' in update_data or 'start_time' in update_data or 'end_time' in update_data:
            new_table_id = update_data.get('table_id', db_booking.table_id)
            new_start = update_data.get('start_time', db_booking.start_time)
            new_end = update_data.get('end_time', db_booking.end_time)
            
            # Convert strings to datetime objects if necessary
            if isinstance(new_start, str):
                new_start = datetime.fromisoformat(new_start)
            if isinstance(new_end, str):
                new_end = datetime.fromisoformat(new_end)
            
            # Duration validation
            duration = (new_end - new_start).total_seconds() / 60
            if duration < settings.MIN_BOOKING_DURATION or duration > settings.MAX_BOOKING_DURATION:
                return "duration_error"

            # To avoid overlapping with itself, we can't just use is_table_available.
            # A simple way for a course project: check if ANY other booking overlaps.
            overlapping = db.query(models.Booking).filter(
                models.Booking.id != booking_id,
                models.Booking.table_id == new_table_id,
                models.Booking.start_time < new_end,
                models.Booking.end_time > new_start
            ).first()
            
            if overlapping:
                return "unavailable"
            
            # Update the values in update_data to the converted datetimes so they are saved correctly
            if 'start_time' in update_data:
                update_data['start_time'] = new_start
            if 'end_time' in update_data:
                update_data['end_time'] = new_end

        for key, value in update_data.items():
            setattr(db_booking, key, value)
        
        db.commit()
        db.refresh(db_booking)
        return db_booking

    @staticmethod
    def get_all_bookings(db: Session):
        return db.query(models.Booking).all()

    @staticmethod
    def get_table_availability(db: Session, table_id: int, date: datetime):
        return db.query(models.Booking).filter(
            models.Booking.table_id == table_id,
            models.Booking.start_time >= date.replace(hour=0, minute=0, second=0),
            models.Booking.end_time <= date.replace(hour=23, minute=59, second=59)
        ).all()


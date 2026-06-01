from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas import booking as schemas
from app.services.booking_service import BookingService
from .auth import get_current_user, check_admin_role
from app.models import booking as models
from app.models.user import User, UserRole
from app.services.notification_service import send_booking_notification
from app.core.config import settings
from datetime import datetime, time

router = APIRouter()

@router.get("/my", response_model=list[schemas.BookingRead])
def get_my_bookings(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return db.query(models.Booking).filter(models.Booking.user_id == current_user.id).all()

@router.get("/availability", response_model=list[int])
def get_availability(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    start_time: str = Query(..., description="Start time in HH:MM format"),
    end_time: str = Query(..., description="End time in HH:MM format"),
    db: Session = Depends(get_db)
):
    try:
        # Parse input strings into datetime objects
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")

    # Get all tables
    all_tables = db.query(models.Table).all()
    available_tables = []

    for table in all_tables:
        if BookingService.is_table_available(db, table.id, start_dt, end_dt):
            available_tables.append(table.id)

    return available_tables

@router.post("/", response_model=schemas.BookingRead)
def create_booking(
    booking: schemas.BookingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    result = BookingService.create_booking(db, booking, user_id=current_user.id)
    if result == "duration_error":
        raise HTTPException(
            status_code=400, 
            detail=f"Booking duration must be between {settings.MIN_BOOKING_DURATION} and {settings.MAX_BOOKING_DURATION} minutes"
        )
    if not result:
        raise HTTPException(status_code=400, detail="Table is not available for the selected time interval")
    
    # Get table number for notification
    table = db.query(models.Table).filter(models.Table.id == result.table_id).first()
    background_tasks.add_task(
        send_booking_notification, 
        result.customer_name, 
        table.number, 
        result.start_time
    )
    
    return result

@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Only owner or admin can cancel
    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")

    if not BookingService.cancel_booking(db, booking_id):
        raise HTTPException(status_code=500, detail="Error canceling booking")
    return {"detail": "Booking cancelled"}

@router.get("/admin/all", response_model=list[schemas.BookingRead])
def get_all_bookings_admin(
    db: Session = Depends(get_db), 
    admin: User = Depends(check_admin_role)
):
    # Join with User to get the phone number
    bookings = db.query(models.Booking).join(User).all()

    # Map phone number to the booking object for the schema
    for b in bookings:
        b.user_phone = b.user.phone if b.user else None

    return bookings

@router.get("/admin/search", response_model=list[schemas.BookingRead])
def search_bookings_by_phone(
    phone: str = Query(..., description="User phone number to search"),
    db: Session = Depends(get_db), 
    admin: User = Depends(check_admin_role)
):
    # Join with User to get the phone number
    bookings = db.query(models.Booking).join(User).filter(User.phone == phone).all()

    for b in bookings:
        b.user_phone = b.user.phone if b.user else None

    return bookings

@router.patch("/admin/{booking_id}", response_model=schemas.BookingRead)
def update_booking_admin(
    booking_id: int, 
    update_data: dict = Body(...),
    db: Session = Depends(get_db), 
    admin: User = Depends(check_admin_role)
):
    result = BookingService.update_booking(db, booking_id, update_data)
    if result == "unavailable":
        raise HTTPException(status_code=400, detail="Table is not available for the new time interval")
    if result == "duration_error":
        raise HTTPException(
            status_code=400, 
            detail=f"Booking duration must be between {settings.MIN_BOOKING_DURATION} and {settings.MAX_BOOKING_DURATION} minutes"
        )
    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")
    return result

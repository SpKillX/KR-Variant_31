from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas import booking as schemas
from app.services.booking_service import BookingService
from .auth import get_current_user
from app.models import booking as models
from app.models.user import User
from app.services.notification_service import send_booking_notification
from datetime import datetime, time

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
    if not BookingService.cancel_booking(db, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"detail": "Booking cancelled"}

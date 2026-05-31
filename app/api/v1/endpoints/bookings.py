from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas import booking as schemas
from app.services.booking_service import BookingService
from .auth import get_current_user
from app.models.user import User
from app.services.notification_service import send_booking_notification

router = APIRouter()

@router.post("/", response_model=schemas.BookingRead)
def create_booking(
    booking: schemas.BookingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    result = BookingService.create_booking(db, booking)
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

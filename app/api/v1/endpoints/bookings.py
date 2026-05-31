from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
<<<<<<< Updated upstream
from ...db.session import get_db
from ...schemas import booking as schemas
from ...services.booking_service import BookingService
=======
from app.db.session import get_db
from app.schemas import booking as schemas
from app.services.booking_service import BookingService
from .auth import get_current_user
from app.models.user import User
from app.services.notification_service import send_booking_notification
>>>>>>> Stashed changes

router = APIRouter()

@router.post("/", response_model=schemas.BookingRead)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    result = BookingService.create_booking(db, booking)
    if not result:
        raise HTTPException(status_code=400, detail="Table is not available for the selected time interval")
    return result

@router.delete("/{booking_id}")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    if not BookingService.cancel_booking(db, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"detail": "Booking cancelled"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...schemas import booking as schemas
from ...services.booking_service import BookingService

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

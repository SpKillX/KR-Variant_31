from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas import booking as schemas
from app.services.restaurant_service import RestaurantService

router = APIRouter()

@router.get("/", response_model=list[schemas.RestaurantRead])
def get_restaurants(db: Session = Depends(get_db)):
    return RestaurantService.get_all_restaurants(db)

@router.get("/{restaurant_id}/zones", response_model=list[schemas.ZoneRead])
def get_zones(restaurant_id: int, db: Session = Depends(get_db)):
    return RestaurantService.get_zones_by_restaurant(db, restaurant_id)

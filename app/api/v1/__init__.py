from fastapi import APIRouter
from .endpoints import restaurants, bookings, auth

api_router = APIRouter()

# Подключаем модули с соответствующими префиксами
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(restaurants.router, prefix="/restaurants", tags=["Restaurants"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])

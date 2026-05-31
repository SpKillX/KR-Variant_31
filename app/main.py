from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime
import time

from .db.session import Base, engine, get_db, SessionLocal
from .models import booking as models
from .api.v1 import api_router

# Simulation of a notification system
def send_booking_notification(customer_name: str, table_number: int, start_time: datetime):
    # In a real app, this would call an SMS/Email API (e.g., Twilio, SendGrid)
    print(f"--- NOTIFICATION SYSTEM ---")
    print(f"Sending confirmation to {customer_name}...")
    time.sleep(2) # Simulate network delay
    print(f"SUCCESS: Table {table_number} reserved for {start_time}. Notification sent!")
    print(f"--------------------------")

# Initialize database tables
Base.metadata.create_all(bind=engine)
def seed_data(db: Session):
    if db.query(models.Restaurant).first():
        return

    # 1. Create Restaurants with Tula addresses
    res1 = models.Restaurant(name="Гурман", address="ул. Фридерика Энгельса, 15, Тула")
    res2 = models.Restaurant(name="Звезда", address="пр. Ленина, 40, Тула")
    db.add_all([res1, res2])
    db.commit()

    # 2. Create Zones
    zone1 = models.Zone(restaurant_id=res1.id, name="Основной зал")
    zone2 = models.Zone(restaurant_id=res1.id, name="Терраса")
    zone3 = models.Zone(restaurant_id=res2.id, name="VIP-зал")
    db.add_all([zone1, zone2, zone3])
    db.commit()

    # 3. Create Tables with coordinates
    tables1 = [
        models.Table(zone_id=zone1.id, number=1, capacity=2, x_coord=10.0, y_coord=10.0),
        models.Table(zone_id=zone1.id, number=2, capacity=2, x_coord=20.0, y_coord=10.0),
        models.Table(zone_id=zone1.id, number=3, capacity=4, x_coord=10.0, y_coord=20.0),
        models.Table(zone_id=zone2.id, number=4, capacity=2, x_coord=50.0, y_coord=50.0),
    ]

    tables2 = [
        models.Table(zone_id=zone3.id, number=1, capacity=6, x_coord=100.0, y_coord=100.0),
        models.Table(zone_id=zone3.id, number=2, capacity=6, x_coord=120.0, y_coord=100.0),
    ]

    db.add_all(tables1 + tables2)
    db.commit()

    # 4. Create Default Admin User
    from .core.security import get_password_hash
    from .models import user as user_models

    if not db.query(user_models.User).filter(user_models.User.username == "admin").first():
        admin_user = user_models.User(
            username="admin",
            hashed_password=get_password_hash("password"),
            role=user_models.UserRole.ADMIN
        )
        db.add(admin_user)
        db.commit()

async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        seed_data(db)
    yield

app = FastAPI(title="Restaurant Booking System", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Подключаем все API эндпоинты
app.include_router(api_router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

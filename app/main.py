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
    # 1. Seed Restaurants, Zones and Tables (only if DB is empty)
    if not db.query(models.Restaurant).first():
        res1 = models.Restaurant(name="Гурман", address="пр. Ленина 92, Тула", opening_time="09:00", closing_time="23:00")
        res2 = models.Restaurant(name="Звезда", address="Советская 47, Тула", opening_time="10:00", closing_time="00:00")
        db.add_all([res1, res2])
        db.commit()

        # Zones for Restaurant 1
        z1_1 = models.Zone(restaurant_id=res1.id, name="Основной зал")
        z1_2 = models.Zone(restaurant_id=res1.id, name="Летняя терраса")
        z1_3 = models.Zone(restaurant_id=res1.id, name="VIP-кабинеты")

        # Zones for Restaurant 2
        z2_1 = models.Zone(restaurant_id=res2.id, name="Главный зал")
        z2_2 = models.Zone(restaurant_id=res2.id, name="Зимний сад")
        z2_3 = models.Zone(restaurant_id=res2.id, name="Банкетный зал")

        db.add_all([z1_1, z1_2, z1_3, z2_1, z2_2, z2_3])
        db.commit()

        # Tables for Restaurant 1 - Main Hall
        tables1_1 = [
            models.Table(zone_id=z1_1.id, number=1, capacity=2, x_coord=80, y_coord=80),
            models.Table(zone_id=z1_1.id, number=2, capacity=2, x_coord=200, y_coord=80),
            models.Table(zone_id=z1_1.id, number=3, capacity=4, x_coord=80, y_coord=180),
            models.Table(zone_id=z1_1.id, number=4, capacity=4, x_coord=200, y_coord=180),
            models.Table(zone_id=z1_1.id, number=5, capacity=6, x_coord=350, y_coord=130),
        ]
        # Tables for Restaurant 1 - Terrace
        tables1_2 = [
            models.Table(zone_id=z1_2.id, number=6, capacity=2, x_coord=100, y_coord=50),
            models.Table(zone_id=z1_2.id, number=7, capacity=2, x_coord=250, y_coord=50),
            models.Table(zone_id=z1_2.id, number=8, capacity=4, x_coord=400, y_coord=50),
        ]
        # Tables for Restaurant 1 - VIP
        tables1_3 = [
            models.Table(zone_id=z1_3.id, number=9, capacity=4, x_coord=150, y_coord=100),
            models.Table(zone_id=z1_3.id, number=10, capacity=6, x_coord=300, y_coord=100),
        ]

        # Tables for Restaurant 2 - Main Hall
        tables2_1 = [
            models.Table(zone_id=z2_1.id, number=1, capacity=2, x_coord=100, y_coord=100),
            models.Table(zone_id=z2_1.id, number=2, capacity=2, x_coord=250, y_coord=100),
            models.Table(zone_id=z2_1.id, number=3, capacity=4, x_coord=100, y_coord=200),
            models.Table(zone_id=z2_1.id, number=4, capacity=4, x_coord=250, y_coord=200),
        ]
        # Tables for Restaurant 2 - Winter Garden
        tables2_2 = [
            models.Table(zone_id=z2_2.id, number=5, capacity=2, x_coord=50, y_coord=50),
            models.Table(zone_id=z2_2.id, number=6, capacity=2, x_coord=150, y_coord=50),
            models.Table(zone_id=z2_2.id, number=7, capacity=4, x_coord=250, y_coord=50),
        ]
        # Tables for Restaurant 2 - Banquet Hall
        tables2_3 = [
            models.Table(zone_id=z2_3.id, number=8, capacity=8, x_coord=200, y_coord=150),
            models.Table(zone_id=z2_3.id, number=9, capacity=10, x_coord=400, y_coord=150),
        ]

        db.add_all(tables1_1 + tables1_2 + tables1_3 + tables2_1 + tables2_2 + tables2_3)
        db.commit()

    # 2. Always ensure Default Admin User exists
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

@asynccontextmanager
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

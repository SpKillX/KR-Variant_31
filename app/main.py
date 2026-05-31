from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import datetime

from .db.session import Base, engine, get_db, SessionLocal
from .models import booking as models
from .schemas import booking as schemas
from .services import booking_service as crud

# Initialize database tables
Base.metadata.create_all(bind=engine)

def seed_data(db: Session):
    if db.query(models.Restaurant).first():
        return

    res1 = models.Restaurant(name="Гурман", address="ул. Пушкина, 10")
    res2 = models.Restaurant(name="Звезда", address="пр. Ленина, 25")
    db.add_all([res1, res2])
    db.commit()

    tables1 = [
        models.Table(restaurant_id=res1.id, number=1, capacity=2, is_available=True),
        models.Table(restaurant_id=res1.id, number=2, capacity=2, is_available=False),
        models.Table(restaurant_id=res1.id, number=3, capacity=4, is_available=True),
        models.Table(restaurant_id=res1.id, number=4, capacity=4, is_available=True),
        models.Table(restaurant_id=res1.id, number=5, capacity=6, is_available=True),
        models.Table(restaurant_id=res1.id, number=6, capacity=2, is_available=True),
    ]
    
    tables2 = [
        models.Table(restaurant_id=res2.id, number=1, capacity=2, is_available=True),
        models.Table(restaurant_id=res2.id, number=2, capacity=2, is_available=True),
        models.Table(restaurant_id=res2.id, number=3, capacity=4, is_available=False),
        models.Table(restaurant_id=res2.id, number=4, capacity=4, is_available=False),
        models.Table(restaurant_id=res2.id, number=5, capacity=6, is_available=True),
        models.Table(restaurant_id=res2.id, number=6, capacity=6, is_available=True),
        models.Table(restaurant_id=res2.id, number=7, capacity=2, is_available=True),
        models.Table(restaurant_id=res2.id, number=8, capacity=2, is_available=True),
    ]
    
    db.add_all(tables1 + tables2)
    db.commit()

    occupied_tables = db.query(models.Table).filter(models.Table.is_available == False).all()
    for t in occupied_tables:
        booking = models.Booking(table_id=t.id, customer_name="Тестовый клиент", booking_time=datetime.utcnow())
        db.add(booking)
    
    db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        seed_data(db)
    yield

app = FastAPI(title="Restaurant Booking System", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/restaurants", response_model=list[schemas.RestaurantRead])
def get_restaurants(db: Session = Depends(get_db)):
    return crud.get_restaurants(db)

@app.get("/api/restaurants/{restaurant_id}/tables", response_model=list[schemas.TableRead])
def get_tables(restaurant_id: int, db: Session = Depends(get_db)):
    return crud.get_tables_by_restaurant(db, restaurant_id)

@app.post("/api/bookings", response_model=schemas.BookingRead)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    result = crud.create_booking(db, booking)
    if not result:
        raise HTTPException(status_code=400, detail="Table is not available")
    return result

@app.delete("/api/bookings/{booking_id}")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    if not crud.cancel_booking(db, booking_id):
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"detail": "Booking cancelled"}

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Restaurant, Table

# Use a separate SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    # Create test data
    db = TestingSessionLocal()
    res = Restaurant(name="Test Rest", address="Test St")
    db.add(res)
    db.commit()
    
    t1 = Table(restaurant_id=res.id, number=1, capacity=2, is_available=True)
    t2 = Table(restaurant_id=res.id, number=2, capacity=4, is_available=False)
    db.add_all([t1, t2])
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)
    db.close()

def test_get_restaurants():
    response = client.get("/api/restaurants")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Test Rest"

def test_get_tables():
    # First get restaurant ID
    res = client.get("/api/restaurants").json()[0]
    response = client.get(f"/api/restaurants/{res['id']}/tables")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_create_booking_success():
    res = client.get("/api/restaurants").json()[0]
    tables = client.get(f"/api/restaurants/{res['id']}/tables").json()
    available_table = next(t for t in tables if t["is_available"])
    
    payload = {
        "table_id": available_table["id"],
        "customer_name": "Test User",
        "booking_time": "2026-05-31T12:00:00"
    }
    response = client.post("/api/bookings", json=payload)
    assert response.status_code == 200
    assert response.json()["customer_name"] == "Test User"

def test_create_booking_unavailable():
    res = client.get("/api/restaurants").json()[0]
    tables = client.get(f"/api/restaurants/{res['id']}/tables").json()
    occupied_table = next(t for t in tables if not t["is_available"])
    
    payload = {
        "table_id": occupied_table["id"],
        "customer_name": "Test User",
        "booking_time": "2026-05-31T12:00:00"
    }
    response = client.post("/api/bookings", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Table is not available"

def test_cancel_booking():
    # Create a booking first
    res = client.get("/api/restaurants").json()[0]
    tables = client.get(f"/api/restaurants/{res['id']}/tables").json()
    table = next(t for t in tables if t["is_available"])
    
    booking = client.post("/api/bookings", json={
        "table_id": table["id"],
        "customer_name": "Cancel Me",
        "booking_time": "2026-05-31T12:00:00"
    }).json()
    
    response = client.delete(f"/api/bookings/{booking['id']}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Booking cancelled"

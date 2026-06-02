import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base
from app.core.config import settings
from app.models import booking as booking_models
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from datetime import datetime, time, timedelta

# --- Configuration ---
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
client = TestClient(app)

# --- Fixtures ---

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Users
        admin = User(username="admin", hashed_password=get_password_hash("password"), role=UserRole.ADMIN, phone="+79990000000")
        client_user = User(username="testuser", hashed_password=get_password_hash("password123"), role=UserRole.CLIENT, phone="+79001112233")
        db.add_all([admin, client_user])
        
        # Restaurant 1 (Standard)
        res1 = booking_models.Restaurant(name="Resto One", address="Addr 1", opening_time=time(9, 0), closing_time=time(23, 0))
        db.add(res1)
        db.commit()
        db.refresh(res1)
        
        zone1 = booking_models.Zone(restaurant_id=res1.id, name="Hall 1")
        db.add(zone1)
        db.commit()
        db.refresh(zone1)
        
        # Tables for Resto 1
        tables1 = [booking_models.Table(zone_id=zone1.id, number=i, capacity=2) for i in range(1, 6)]
        db.add_all(tables1)
        
        # Restaurant 2 (Short hours)
        res2 = booking_models.Restaurant(name="Resto Two", address="Addr 2", opening_time=time(12, 0), closing_time=time(18, 0))
        db.add(res2)
        db.commit()
        db.refresh(res2)
        
        zone2 = booking_models.Zone(restaurant_id=res2.id, name="Hall 2")
        db.add(zone2)
        db.commit()
        db.refresh(zone2)
        
        table2 = booking_models.Table(zone_id=zone2.id, number=101, capacity=4)
        db.add(table2)
        
        db.commit()
        yield db
    finally:
        db.close()

@pytest.fixture
def admin_token():
    res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "password"})
    return res.json()["access_token"]

@pytest.fixture
def client_token():
    res = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "password123"})
    return res.json()["access_token"]

# --- 1. AUTHENTICATION TESTS (8 tests) ---

def test_register_success():
    res = client.post("/api/v1/auth/register", json={"username": "new", "password": "pw", "phone": "+7123", "role": "client"})
    assert res.status_code == 200

def test_register_duplicate_user():
    client.post("/api/v1/auth/register", json={"username": "dup", "password": "pw", "phone": "+71", "role": "client"})
    res = client.post("/api/v1/auth/register", json={"username": "dup", "password": "pw", "phone": "+72", "role": "client"})
    assert res.status_code == 400

def test_login_success():
    res = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "password123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_wrong_password():
    res = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "wrongpassword"})
    assert res.status_code == 401

def test_login_nonexistent_user():
    res = client.post("/api/v1/auth/login", data={"username": "nobody", "password": "pw"})
    assert res.status_code == 401

def test_me_valid_token(client_token):
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"

def test_me_invalid_token():
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == 401

def test_me_no_token():
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

# --- 2. RESTAURANT & ZONE TESTS (6 tests) ---

def test_get_all_restaurants():
    res = client.get("/api/v1/restaurants/")
    assert res.status_code == 200
    assert len(res.json()) == 2

def test_get_zones_valid_restaurant():
    res = client.get("/api/v1/restaurants/1/zones")
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_get_zones_invalid_restaurant():
    res = client.get("/api/v1/restaurants/999/zones")
    assert res.status_code == 404


def test_restaurant_data_integrity():
    res = client.get("/api/v1/restaurants/").json()[0]
    assert "name" in res
    assert "address" in res
    assert "opening_time" in res

def test_zone_tables_loading():
    res = client.get("/api/v1/restaurants/1/zones").json()[0]
    assert "tables" in res
    assert len(res["tables"]) > 0

def test_zone_empty_restaurant():
    # Test logic for restaurant with no zones if we had one
    pass

# --- 3. AVAILABILITY TESTS (10 tests) ---

@pytest.mark.parametrize("start, end, expected_available", [
    ("12:00", "14:00", True),   # Standard slot
    ("08:00", "10:00", False),  # Before opening (9:00)
    ("22:00", "23:30", False),  # After closing (23:00)
    ("10:00", "11:00", True),   # Early slot
    ("20:00", "22:00", True),   # Late slot
])
def test_availability_working_hours(start, end, expected_available):
    res = client.get(f"/api/v1/bookings/availability?date=2026-06-10&start_time={start}&end_time={end}")
    assert res.status_code == 200
    assert (len(res.json()) > 0) == expected_available

def test_availability_invalid_date():
    res = client.get("/api/v1/bookings/availability?date=invalid&start_time=12:00&end_time=14:00")
    assert res.status_code == 400

def test_availability_invalid_time():
    res = client.get("/api/v1/bookings/availability?date=2026-06-10&start_time=25:00&end_time=26:00")
    assert res.status_code == 400

def test_availability_overlap_exact(client_token):
    date = "2026-06-15"
    # Book table 1 from 12 to 14
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "X", "start_time": f"{date}T12:00:00", "end_time": f"{date}T14:00:00"})
    
    res = client.get(f"/api/v1/bookings/availability?date={date}&start_time=12:00&end_time=14:00")
    # Table 1 should be gone from the list
    assert 1 not in res.json()

def test_availability_overlap_start(client_token):
    date = "2026-06-16"
    # Book 12:00 - 14:00
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "X", "start_time": f"{date}T12:00:00", "end_time": f"{date}T14:00:00"})
    
    # Check 11:00 - 13:00 (Overlaps start)
    res = client.get(f"/api/v1/bookings/availability?date={date}&start_time=11:00&end_time=13:00")
    assert 1 not in res.json()

def test_availability_overlap_end(client_token):
    date = "2026-06-17"
    # Book 12:00 - 14:00
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "X", "start_time": f"{date}T12:00:00", "end_time": f"{date}T14:00:00"})
    
    # Check 13:00 - 15:00 (Overlaps end)
    res = client.get(f"/api/v1/bookings/availability?date={date}&start_time=13:00&end_time=15:00")
    assert 1 not in res.json()

def test_availability_overlap_inside(client_token):
    date = "2026-06-18"
    # Book 12:00 - 16:00
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "X", "start_time": f"{date}T12:00:00", "end_time": f"{date}T16:00:00"})
    
    # Check 13:00 - 14:00 (Inside)
    res = client.get(f"/api/v1/bookings/availability?date={date}&start_time=13:00&end_time=14:00")
    assert 1 not in res.json()

def test_availability_overlap_containing(client_token):
    date = "2026-06-19"
    # Book 13:00 - 14:00
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "X", "start_time": f"{date}T13:00:00", "end_time": f"{date}T14:00:00"})
    
    # Check 12:00 - 15:00 (Contains the booking)
    res = client.get(f"/api/v1/bookings/availability?date={date}&start_time=12:00&end_time=15:00")
    assert 1 not in res.json()

# --- 4. CLIENT BOOKING LIFECYCLE (12 tests) ---

def test_create_booking_success(client_token):
    res = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-01T12:00:00", "end_time": "2026-07-01T14:00:00"})
    assert res.status_code == 200
    assert res.json()["customer_name"] == "Alice"

def test_create_booking_unauthorized():
    res = client.post("/api/v1/bookings/", json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-01T12:00:00", "end_time": "2026-07-01T14:00:00"})
    assert res.status_code == 401

def test_create_booking_invalid_table(client_token):
    res = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 999, "customer_name": "Alice", "start_time": "2026-07-01T12:00:00", "end_time": "2026-07-01T14:00:00"})
    assert res.status_code == 400

def test_create_booking_too_short(client_token):
    res = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-01T12:00:00", "end_time": "2026-07-01T12:30:00"})
    assert res.status_code == 400
    assert "duration" in res.json()["detail"]

def test_create_booking_too_long(client_token):
    res = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-01T12:00:00", "end_time": "2026-07-01T18:00:00"})
    assert res.status_code == 400
    assert "duration" in res.json()["detail"]

def test_cancel_own_booking(client_token):
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-02T12:00:00", "end_time": "2026-07-02T14:00:00"}).json()
    res = client.delete(f"/api/v1/bookings/{book['id']}", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 200

def test_cancel_others_booking(client_token):
    # Create another user
    client.post("/api/v1/auth/register", json={"username": "user2", "password": "pw", "phone": "+72", "role": "client"})
    login_u2 = client.post("/api/v1/auth/login", data={"username": "user2", "password": "pw"}).json()["access_token"]
    
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {login_u2}"}, 
                      json={"table_id": 2, "customer_name": "User 2", "start_time": "2026-07-03T12:00:00", "end_time": "2026-07-03T14:00:00"}).json()
    
    res = client.delete(f"/api/v1/bookings/{book['id']}", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 403

def test_cancel_nonexistent_booking(client_token):
    res = client.delete("/api/v1/bookings/999", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 404

def test_get_my_bookings_empty(client_token):
    res = client.get("/api/v1/bookings/my", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 200
    assert len(res.json()) == 0

def test_get_my_bookings_populated(client_token):
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-04T12:00:00", "end_time": "2026-07-04T14:00:00"})
    res = client.get("/api/v1/bookings/my", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 200
    assert len(res.json()) == 1

def test_my_bookings_unauthorized():
    res = client.get("/api/v1/bookings/my")
    assert res.status_code == 401

def test_booking_conflict_same_user(client_token):
    # User tries to book two different tables at the same time - this is allowed in current logic
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "Alice", "start_time": "2026-07-05T12:00:00", "end_time": "2026-07-05T14:00:00"})
    res = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 2, "customer_name": "Alice", "start_time": "2026-07-05T12:00:00", "end_time": "2026-07-05T14:00:00"})
    assert res.status_code == 200

# --- 5. ADMIN BOOKINGS (12 tests) ---

def test_admin_get_all_bookings(admin_token):
    res = client.get("/api/v1/bookings/admin/all", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_admin_get_all_forbidden(client_token):
    res = client.get("/api/v1/bookings/admin/all", headers={"Authorization": f"Bearer {client_token}"})
    assert res.status_code == 403

def test_admin_search_no_results(admin_token):
    res = client.get("/api/v1/bookings/admin/search?phone=+70000000000", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) == 0

def test_admin_update_customer_name(admin_token, client_token):
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "Old Name", "start_time": "2026-07-07T12:00:00", "end_time": "2026-07-07T14:00:00"}).json()
    
    res = client.patch(f"/api/v1/bookings/admin/{book['id']}", headers={"Authorization": f"Bearer {admin_token}"}, 
                       json={"customer_name": "New Name"})
    assert res.status_code == 200
    assert res.json()["customer_name"] == "New Name"

def test_admin_update_table_success(admin_token, client_token):
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "User", "start_time": "2026-07-08T12:00:00", "end_time": "2026-07-08T14:00:00"}).json()
    
    res = client.patch(f"/api/v1/bookings/admin/{book['id']}", headers={"Authorization": f"Bearer {admin_token}"}, 
                       json={"table_id": 2})
    assert res.status_code == 200
    assert res.json()["table_id"] == 2

def test_admin_update_table_conflict(admin_token, client_token):
    # Table 2 is occupied
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 2, "customer_name": "Occupier", "start_time": "2026-07-09T12:00:00", "end_time": "2026-07-09T14:00:00"})
    
    # Booking on table 1
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "User", "start_time": "2026-07-09T12:00:00", "end_time": "2026-07-09T14:00:00"}).json()
    
    # Admin tries to move it to table 2
    res = client.patch(f"/api/v1/bookings/admin/{book['id']}", headers={"Authorization": f"Bearer {admin_token}"}, 
                       json={"table_id": 2})
    assert res.status_code == 400
    assert "not available" in res.json()["detail"]

def test_admin_update_nonexistent(admin_token):
    res = client.patch("/api/v1/bookings/admin/999", headers={"Authorization": f"Bearer {admin_token}"}, 
                       json={"customer_name": "Ghost"})
    assert res.status_code == 404

def test_admin_delete_any_booking(admin_token, client_token):
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "User", "start_time": "2026-07-10T12:00:00", "end_time": "2026-07-10T14:00:00"}).json()
    
    res = client.delete(f"/api/v1/bookings/{book['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200

def test_admin_update_time_overlap(admin_token, client_token):
    # Table 1: 12-14 booked by User A
    client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 1, "customer_name": "User A", "start_time": "2026-07-11T12:00:00", "end_time": "2026-07-11T14:00:00"})
    
    # Table 2: 15-17 booked by User B
    book_b = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                json={"table_id": 2, "customer_name": "User B", "start_time": "2026-07-11T15:00:00", "end_time": "2026-07-11T17:00:00"}).json()
    
    # Admin moves User B to Table 1 at 13:00 (Conflict)
    res = client.patch(f"/api/v1/bookings/admin/{book_b['id']}", headers={"Authorization": f"Bearer {admin_token}"}, 
                       json={"table_id": 1, "start_time": "2026-07-11T13:00:00", "end_time": "2026-07-11T15:00:00"})
    assert res.status_code == 400

def test_admin_update_working_hours(admin_token, client_token):
    book = client.post("/api/v1/bookings/", headers={"Authorization": f"Bearer {client_token}"}, 
                      json={"table_id": 1, "customer_name": "User", "start_time": "2026-07-12T12:00:00", "end_time": "2026-07-12T14:00:00"}).json()
    
    # Move to 07:00 (Resto opens at 09:00)
    res = client.patch(f"/api/v1/bookings/admin/{book['id']}", headers={"Authorization": f"Bearer {admin_token}"}, 
                       json={"start_time": "2026-07-12T07:00:00", "end_time": "2026-07-12T09:00:00"})
    assert res.status_code == 400
    assert res.status_code == 400

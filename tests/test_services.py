import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, time, timedelta
from app.services.booking_service import BookingService
from app.models import booking as models
from app.models.user import User
from app.schemas import booking as schemas
from app.core.config import settings

# --- Mocks & Fixtures ---

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_restaurant():
    return models.Restaurant(
        id=1, 
        name="Test Resto", 
        opening_time=time(9, 0), 
        closing_time=time(23, 0)
    )

@pytest.fixture
def mock_zone():
    return models.Zone(id=1, restaurant_id=1, name="Main Hall")

@pytest.fixture
def mock_table():
    return models.Table(id=1, zone_id=1, number=10, capacity=2)

# --- Tests for is_table_available ---

def test_is_table_available_success(mock_db, mock_table, mock_zone, mock_restaurant):
    start_dt = datetime(2026, 6, 10, 12, 0)
    end_dt = datetime(2026, 6, 10, 14, 0)

    # Unified mock for all .first() calls in is_table_available
    mock_db.query.return_value.filter.return_value.first = MagicMock(side_effect=[
        mock_table,      # 1. Table
        mock_zone,       # 2. Zone
        mock_restaurant, # 3. Restaurant
        None             # 4. Overlap check
    ])

    assert BookingService.is_table_available(mock_db, mock_table.id, start_dt, end_dt) is True

def test_is_table_available_outside_working_hours(mock_db, mock_table, mock_zone, mock_restaurant):
    start_dt = datetime(2026, 6, 10, 8, 0)
    end_dt = datetime(2026, 6, 10, 10, 0)

    mock_db.query.return_value.filter.return_value.first = MagicMock(side_effect=[
        mock_table,
        mock_zone,
        mock_restaurant
    ])

    assert BookingService.is_table_available(mock_db, mock_table.id, start_dt, end_dt) is False

def test_is_table_available_overlap(mock_db, mock_table, mock_zone, mock_restaurant):
    start_dt = datetime(2026, 6, 10, 12, 0)
    end_dt = datetime(2026, 6, 10, 14, 0)

    mock_db.query.return_value.filter.return_value.first = MagicMock(side_effect=[
        mock_table,
        mock_zone,
        mock_restaurant,
        MagicMock() # Overlap found
    ])

    assert BookingService.is_table_available(mock_db, mock_table.id, start_dt, end_dt) is False

# --- Tests for create_booking ---

def test_create_booking_duration_too_short(mock_db):
    booking_data = schemas.BookingCreate(
        table_id=1,
        customer_name="Alice",
        start_time=datetime(2026, 6, 10, 12, 0),
        end_time=datetime(2026, 6, 10, 12, 10)
    )
    
    result = BookingService.create_booking(mock_db, booking_data)
    assert result == "duration_error"

def test_create_booking_unavailable(mock_db):
    booking_data = schemas.BookingCreate(
        table_id=1,
        customer_name="Alice",
        start_time=datetime(2026, 6, 10, 12, 0),
        end_time=datetime(2026, 6, 10, 14, 0)
    )
    
    with patch('app.services.booking_service.BookingService.is_table_available', return_value=False):
        result = BookingService.create_booking(mock_db, booking_data)
        assert result is None

def test_create_booking_success(mock_db):
    booking_data = schemas.BookingCreate(
        table_id=1,
        customer_name="Alice",
        start_time=datetime(2026, 6, 10, 12, 0),
        end_time=datetime(2026, 6, 10, 14, 0)
    )
    
    with patch('app.services.booking_service.BookingService.is_table_available', return_value=True):
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        result = BookingService.create_booking(mock_db, booking_data)
        assert isinstance(result, models.Booking)
        assert result.customer_name == "Alice"

# --- Tests for update_booking ---

def test_update_booking_unavailable(mock_db):
    existing_booking = models.Booking(id=1, table_id=1, start_time=datetime(2026, 6, 10, 12, 0), end_time=datetime(2026, 6, 10, 14, 0))
    
    # Mock a sequence of returns for the availability check inside update_booking
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        existing_booking,              # First: find existing booking
        models.Table(id=1, zone_id=1), # Second: check table
        models.Zone(id=1, restaurant_id=1), # Third: check zone
        models.Restaurant(id=1, opening_time=time(9,0), closing_time=time(23,0)), # Fourth: check resto
        MagicMock()                    # Fifth: overlap found!
    ]
    
    update_data = {
        "start_time": datetime(2026, 6, 10, 15, 0),
        "end_time": datetime(2026, 6, 10, 17, 0)
    }
    
    result = BookingService.update_booking(mock_db, 1, update_data)
    assert result == "unavailable"

def test_update_booking_duration_error(mock_db):
    existing_booking = models.Booking(id=1, table_id=1, start_time=datetime(2026, 6, 10, 12, 0), end_time=datetime(2026, 6, 10, 14, 0))
    mock_db.query(models.Booking).filter().first.return_value = existing_booking
    
    update_data = {
        "start_time": datetime(2026, 6, 10, 12, 0),
        "end_time": datetime(2026, 6, 10, 12, 5) # Too short
    }
    
    result = BookingService.update_booking(mock_db, 1, update_data)
    assert result == "duration_error"


def test_update_booking_duration_error(mock_db):
    existing_booking = models.Booking(id=1, table_id=1, start_time=datetime(2026, 6, 10, 12, 0), end_time=datetime(2026, 6, 10, 14, 0))
    mock_db.query(models.Booking).filter().first.return_value = existing_booking
    
    update_data = {
        "start_time": datetime(2026, 6, 10, 12, 0),
        "end_time": datetime(2026, 6, 10, 12, 5)
    }
    
    result = BookingService.update_booking(mock_db, 1, update_data)
    assert result == "duration_error"

def test_update_booking_unavailable(mock_db):
    existing_booking = models.Booking(id=1, table_id=1, start_time=datetime(2026, 6, 10, 12, 0), end_time=datetime(2026, 6, 10, 14, 0))
    
    # First call is to find the booking itself
    # Subsequent calls inside the availability check: Table, Zone, Restaurant, Overlap
    mock_db.query.return_value.filter.return_value.first.side_effect = [
        existing_booking,
        models.Table(id=1, zone_id=1),
        models.Zone(id=1, restaurant_id=1),
        models.Restaurant(id=1, opening_time=time(9,0), closing_time=time(23,0)),
        MagicMock() # Overlap found
    ]
    
    update_data = {
        "start_time": datetime(2026, 6, 10, 15, 0),
        "end_time": datetime(2026, 6, 10, 17, 0)
    }
    
    result = BookingService.update_booking(mock_db, 1, update_data)
    assert result == "unavailable"

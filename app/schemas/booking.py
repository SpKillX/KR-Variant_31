from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class TableBase(BaseModel):
    number: int
    capacity: int
    is_available: bool = True

class TableCreate(TableBase):
    restaurant_id: int

class TableRead(TableBase):
    id: int
    restaurant_id: int
    model_config = ConfigDict(from_attributes=True)

class RestaurantBase(BaseModel):
    name: str
    address: str

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantRead(RestaurantBase):
    id: int
    tables: List[TableRead] = []
    model_config = ConfigDict(from_attributes=True)

class BookingCreate(BaseModel):
    table_id: int
    customer_name: str
    booking_time: datetime

class BookingRead(BaseModel):
    id: int
    table_id: int
    customer_name: str
    booking_time: datetime
    model_config = ConfigDict(from_attributes=True)

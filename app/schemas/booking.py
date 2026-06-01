from pydantic import BaseModel, ConfigDict
from datetime import datetime, time
from typing import List, Optional

class TableBase(BaseModel):
    number: int
    capacity: int
    x_coord: float = 0.0
    y_coord: float = 0.0

class TableCreate(TableBase):
    zone_id: int

class TableRead(TableBase):
    id: int
    zone_id: int
    model_config = ConfigDict(from_attributes=True)

class ZoneBase(BaseModel):
    name: str

class ZoneCreate(ZoneBase):
    restaurant_id: int

class ZoneRead(ZoneBase):
    id: int
    restaurant_id: int
    tables: List[TableRead] = []
    model_config = ConfigDict(from_attributes=True)

class RestaurantBase(BaseModel):
    name: str
    address: str
    opening_time: time
    closing_time: time

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantRead(RestaurantBase):
    id: int
    zones: List[ZoneRead] = []
    model_config = ConfigDict(from_attributes=True)

class BookingCreate(BaseModel):
    table_id: int
    customer_name: str
    start_time: datetime
    end_time: datetime

class BookingRead(BaseModel):
    id: int
    table_id: int
    customer_name: str
    start_time: datetime
    end_time: datetime
    model_config = ConfigDict(from_attributes=True)

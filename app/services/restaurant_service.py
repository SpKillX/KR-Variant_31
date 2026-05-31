from sqlalchemy.orm import Session
from ..models import booking as models
from ..schemas import booking as schemas

class RestaurantService:
    @staticmethod
    def get_all_restaurants(db: Session):
        return db.query(models.Restaurant).all()

    @staticmethod
    def get_restaurant(db: Session, restaurant_id: int):
        return db.query(models.Restaurant).filter(models.Restaurant.id == restaurant_id).first()

    @staticmethod
    def get_tables_in_zone(db: Session, zone_id: int):
        return db.query(models.Table).filter(models.Table.zone_id == zone_id).all()

    @staticmethod
    def get_zones_by_restaurant(db: Session, restaurant_id: int):
        return db.query(models.Zone).filter(models.Zone.restaurant_id == restaurant_id).all()

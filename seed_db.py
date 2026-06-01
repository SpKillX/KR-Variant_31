from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.models import booking as booking_models
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from datetime import datetime, time
import os

def seed_data():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Starting database seeding...")

        # 1. Create Users
        users_data = [
            {"username": "admin", "password": "password", "phone": "+79990000000", "role": UserRole.ADMIN},
            {"username": "client1", "password": "password123", "phone": "+79001112233", "role": UserRole.CLIENT},
            {"username": "client2", "password": "password123", "phone": "+79004445566", "role": UserRole.CLIENT},
            {"username": "client3", "password": "password123", "phone": "+79007778899", "role": UserRole.CLIENT},
            {"username": "client4", "password": "password123", "phone": "+79001110011", "role": UserRole.CLIENT},
            {"username": "client5", "password": "password123", "phone": "+79002220022", "role": UserRole.CLIENT},
            {"username": "client6", "password": "password123", "phone": "+79003330033", "role": UserRole.CLIENT},
        ]

        user_map = {}
        for ud in users_data:
            user = db.query(User).filter(User.username == ud["username"]).first()
            if not user:
                print(f"Creating user: {ud['username']}")
                user = User(
                    username=ud["username"],
                    hashed_password=get_password_hash(ud["password"]),
                    phone=ud["phone"],
                    role=ud["role"]
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            user_map[ud["username"]] = user

        # 2. Create 2 Restaurants
        restaurants_info = [
            {"name": "Gourmet Palace", "address": "ул. Пушкина, 10"},
            {"name": "Ocean View", "address": "наб. Реки, 5"}
        ]
        
        first_table_ids = [] # To store Table #1 ID for each restaurant

        for r_info in restaurants_info:
            res = db.query(booking_models.Restaurant).filter(booking_models.Restaurant.name == r_info["name"]).first()
            if not res:
                print(f"Creating restaurant: {r_info['name']}")
                res = booking_models.Restaurant(
                    name=r_info["name"],
                    address=r_info["address"],
                    opening_time=time(9, 0),
                    closing_time=time(23, 0)
                )
                db.add(res)
                db.commit()
                db.refresh(res)

            zone = db.query(booking_models.Zone).filter(booking_models.Zone.restaurant_id == res.id, booking_models.Zone.name == "Main Hall").first()
            if not zone:
                print(f"Creating Main Hall zone for {res.name}...")
                zone = booking_models.Zone(name="Main Hall", restaurant_id=res.id)
                db.add(zone)
                db.commit()
                db.refresh(zone)

            # Create 5 tables numbered 1-5
            # Check existing tables to avoid duplicates but ensure we have 1-5
            for i in range(1, 6):
                table_exists = db.query(booking_models.Table).filter(
                    booking_models.Table.zone_id == zone.id, 
                    booking_models.Table.number == i
                ).first()
                
                if not table_exists:
                    print(f"Creating Table #{i} for {res.name}...")
                    table = booking_models.Table(
                        number=i,
                        capacity=4 if i < 4 else 6,
                        x_coord=100 * i, # Spaced out to avoid 'in-print' look
                        y_coord=100,
                        zone_id=zone.id
                    )
                    db.add(table)
                else:
                    table = table_exists
                
                if i == 1:
                    first_table_ids.append(table.id)
            
            db.commit()

        # 3. Mandatory Bookings (June 4 - 8, 2026) at 12:00
        # For both restaurants, Table #1
        days = [4, 5, 6, 7, 8]
        users_list = ["client1", "client2", "client3", "client4", "client5"]
        
        for i, day in enumerate(days):
            user_id = user_map[users_list[i % len(users_list)]].id
            customer_name = users_list[i % len(users_list)].capitalize()
            
            start = datetime(2026, 6, day, 12, 0)
            end = datetime(2026, 6, day, 14, 0)
            
            for t_id in first_table_ids:
                exists = db.query(booking_models.Booking).filter(
                    booking_models.Booking.table_id == t_id,
                    booking_models.Booking.start_time == start
                ).first()
                
                if not exists:
                    print(f"Mandatory booking: {customer_name} on {start.date()} at 12:00 for table {t_id}")
                    booking = booking_models.Booking(
                        table_id=t_id,
                        user_id=user_id,
                        customer_name=customer_name,
                        start_time=start,
                        end_time=end
                    )
                    db.add(booking)

        db.commit()
        print("Database seeding completed successfully with 2 restaurants and correctly spaced tables!")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()


if __name__ == "__main__":
    seed_data()

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.models import booking as booking_models
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from datetime import datetime, time
import random

def seed_data():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Cleaning existing data for a fresh start...")
        db.query(booking_models.Booking).delete()
        db.query(booking_models.Table).delete()
        db.query(booking_models.Zone).delete()
        db.query(booking_models.Restaurant).delete()
        db.query(User).delete()
        db.commit()

        # 1. Seed Restaurants, Zones and Tables
        print("Seeding Restaurants, Zones and Tables...")
        
        # Restaurant 1: Гурман
        res1 = booking_models.Restaurant(
            name="Гурман", 
            address="пр. Ленина 92, Тула", 
            opening_time=time(9, 0), 
            closing_time=time(23, 0)
        )
        db.add(res1)
        db.commit()
        db.refresh(res1)

        z1_1 = booking_models.Zone(restaurant_id=res1.id, name="Основной зал")
        z1_2 = booking_models.Zone(restaurant_id=res1.id, name="Летняя терраса")
        z1_3 = booking_models.Zone(restaurant_id=res1.id, name="VIP-кабинеты")
        db.add_all([z1_1, z1_2, z1_3])
        db.commit()

        tables1_1 = [
            booking_models.Table(zone_id=z1_1.id, number=1, capacity=2, x_coord=80, y_coord=80),
            booking_models.Table(zone_id=z1_1.id, number=2, capacity=2, x_coord=200, y_coord=80),
            booking_models.Table(zone_id=z1_1.id, number=3, capacity=4, x_coord=80, y_coord=180),
            booking_models.Table(zone_id=z1_1.id, number=4, capacity=4, x_coord=200, y_coord=180),
            booking_models.Table(zone_id=z1_1.id, number=5, capacity=6, x_coord=350, y_coord=130),
        ]
        tables1_2 = [
            booking_models.Table(zone_id=z1_2.id, number=6, capacity=2, x_coord=100, y_coord=50),
            booking_models.Table(zone_id=z1_2.id, number=7, capacity=2, x_coord=250, y_coord=50),
            booking_models.Table(zone_id=z1_2.id, number=8, capacity=4, x_coord=400, y_coord=50),
        ]
        tables1_3 = [
            booking_models.Table(zone_id=z1_3.id, number=9, capacity=4, x_coord=150, y_coord=100),
            booking_models.Table(zone_id=z1_3.id, number=10, capacity=6, x_coord=300, y_coord=100),
        ]
        db.add_all(tables1_1 + tables1_2 + tables1_3)

        # Restaurant 2: Звезда
        res2 = booking_models.Restaurant(
            name="Звезда", 
            address="Советская 47, Тула", 
            opening_time=time(10, 0), 
            closing_time=time(23, 59)
        )
        db.add(res2)
        db.commit()
        db.refresh(res2)

        z2_1 = booking_models.Zone(restaurant_id=res2.id, name="Главный зал")
        z2_2 = booking_models.Zone(restaurant_id=res2.id, name="Зимний сад")
        z2_3 = booking_models.Zone(restaurant_id=res2.id, name="Банкетный зал")
        db.add_all([z2_1, z2_2, z2_3])
        db.commit()

        tables2_1 = [
            booking_models.Table(zone_id=z2_1.id, number=1, capacity=2, x_coord=100, y_coord=100),
            booking_models.Table(zone_id=z2_1.id, number=2, capacity=2, x_coord=250, y_coord=100),
            booking_models.Table(zone_id=z2_1.id, number=3, capacity=4, x_coord=100, y_coord=200),
            booking_models.Table(zone_id=z2_1.id, number=4, capacity=4, x_coord=250, y_coord=200),
        ]
        tables2_2 = [
            booking_models.Table(zone_id=z2_2.id, number=5, capacity=2, x_coord=50, y_coord=50),
            booking_models.Table(zone_id=z2_2.id, number=6, capacity=2, x_coord=150, y_coord=50),
            booking_models.Table(zone_id=z2_2.id, number=7, capacity=4, x_coord=250, y_coord=50),
        ]
        tables2_3 = [
            booking_models.Table(zone_id=z2_3.id, number=8, capacity=8, x_coord=200, y_coord=150),
            booking_models.Table(zone_id=z2_3.id, number=9, capacity=10, x_coord=400, y_coord=150),
        ]
        db.add_all(tables2_1 + tables2_2 + tables2_3)
        db.commit()

        # 2. Seed Users
        print("Seeding Users...")
        users_data = [
            {"username": "admin", "password": "password", "phone": "+79000000001", "role": UserRole.ADMIN},
            {"username": "ivan", "password": "password123", "phone": "+79000000002", "role": UserRole.CLIENT},
            {"username": "maria", "password": "password123", "phone": "+79000000003", "role": UserRole.CLIENT},
            {"username": "alex", "password": "password123", "phone": "+79000000004", "role": UserRole.CLIENT},
            {"username": "olga", "password": "password123", "phone": "+79000000005", "role": UserRole.CLIENT},
            {"username": "dmitry", "password": "password123", "phone": "+79000000006", "role": UserRole.CLIENT},
        ]
        
        created_users = []
        for ud in users_data:
            user = User(
                username=ud["username"],
                hashed_password=get_password_hash(ud["password"]),
                phone=ud["phone"],
                role=ud["role"]
            )
            db.add(user)
            created_users.append(user)
        db.commit()

        # 3. Seed Bookings
        print("Seeding Bookings (June 5-8, 2026, 12:00-14:00)...")
        client_users = [u for u in created_users if u.role == UserRole.CLIENT]
        all_tables = db.query(booking_models.Table).all()
        
        dates = [5, 6, 7, 8]
        # To track used slots: (date, table_id)
        used_slots = set()

        for user in client_users:
            # 2 to 3 bookings per user
            num_bookings = random.randint(2, 3)
            bookings_created = 0
            
            # Try to find available slots
            attempts = 0
            while bookings_created < num_bookings and attempts < 50:
                attempts += 1
                day = random.choice(dates)
                table = random.choice(all_tables)
                slot = (day, table.id)
                
                if slot not in used_slots:
                    start_dt = datetime(2026, 6, day, 12, 0)
                    end_dt = datetime(2026, 6, day, 14, 0)
                    
                    booking = booking_models.Booking(
                        table_id=table.id,
                        user_id=user.id,
                        customer_name=user.username.capitalize(),
                        start_time=start_dt,
                        end_time=end_dt
                    )
                    db.add(booking)
                    used_slots.add(slot)
                    bookings_created += 1
        
        db.commit()
        print(f"Database seeding completed! Created {len(created_users)} users and {len(used_slots)} bookings.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()

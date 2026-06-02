from app.db.session import SessionLocal
from app.models.user import User
from app.models.booking import Booking

db = SessionLocal()
u = db.query(User).filter(User.username == "searchuser").first()
print(f"User: {u}")
if u:
    print(f"User ID: {u.id}, Phone: {u.phone}")

b = db.query(Booking).filter(Booking.customer_name == "Search Me").first()
print(f"Booking: {b}")
if b:
    print(f"Booking ID: {b.id}, User ID: {b.user_id}")

db.close()

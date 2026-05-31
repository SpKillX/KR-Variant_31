import time
from datetime import datetime

def send_booking_notification(customer_name: str, table_number: int, start_time: datetime):
    """
    Simulates sending a confirmation notification via Email/SMS.
    """
    print(f"--- NOTIFICATION SYSTEM ---")
    print(f"Sending confirmation to {customer_name}...")
    time.sleep(2) # Simulate network delay
    print(f"SUCCESS: Table {table_number} reserved for {start_time}. Notification sent!")
    print(f"--------------------------")

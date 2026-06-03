import time
from datetime import datetime

def send_booking_notification(customer_name: str, table_number: int, start_time: datetime):
    """
    Simulates sending a confirmation notification via Email/SMS.
    Designed to be highly visible in the console for demonstration purposes.
    """
    print("\n" + "="*50)
    print(f"🔔  [NOTIFICATION SYSTEM]  🔔")
    print(f"--------------------------------------------------")
    print(f"👤 Customer: {customer_name}")
    print(f"🪑 Table:    #{table_number}")
    print(f"📅 Time:     {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"--------------------------------------------------")
    print(f"⏳ Sending confirmation... ")
    time.sleep(1.5) 
    print(f"✅ SUCCESS: Notification sent to customer!")
    print("="*50 + "\n")
